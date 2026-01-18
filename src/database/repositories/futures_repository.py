"""
Repository for FuturesTrade model database operations.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import FuturesTrade
from src.core import MAJOR_COINS


class FuturesRepository:
    """Repository for FuturesTrade database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _is_altcoin(self, pair: str) -> bool:
        """Check if a pair is an altcoin (not BTC/ETH/BNB)."""
        # Extract base symbol from pair
        quote_currencies = ["USDT", "USDC", "USD", "BTC", "ETH", "BNB", "BUSD"]
        base_symbol = pair.upper()
        for q in quote_currencies:
            if base_symbol.endswith(q):
                base_symbol = base_symbol[:-len(q)]
                break
        return base_symbol not in MAJOR_COINS

    def _calculate_risk_level(self, leverage: int, is_altcoin: bool) -> str:
        """Calculate risk level based on leverage and coin type."""
        if leverage >= 10:
            return "extreme"
        elif leverage > 3 and is_altcoin:
            return "high"
        elif leverage > 5:
            return "high"
        return "normal"

    async def create(
        self,
        user_id: int,
        pair: str,
        side: str,
        leverage: int,
        entry_price: float,
        quantity: float,
        margin: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        notes: Optional[str] = None
    ) -> FuturesTrade:
        """Create a new futures trade."""
        # Normalize pair to uppercase
        pair = pair.upper().replace("/", "").replace("-", "")
        
        is_altcoin = self._is_altcoin(pair)
        risk_level = self._calculate_risk_level(leverage, is_altcoin)
        
        trade = FuturesTrade(
            user_id=user_id,
            pair=pair,
            side=side.lower(),
            leverage=leverage,
            entry_price=entry_price,
            quantity=quantity,
            margin=margin,
            stop_loss=stop_loss,
            take_profit=take_profit,
            current_price=entry_price,
            is_altcoin=is_altcoin,
            risk_level=risk_level,
            notes=notes,
            status="open"
        )
        self.session.add(trade)
        await self.session.flush()
        return trade

    async def get_by_id(self, trade_id: int) -> Optional[FuturesTrade]:
        """Get trade by ID."""
        result = await self.session.execute(
            select(FuturesTrade).where(FuturesTrade.id == trade_id)
        )
        return result.scalar_one_or_none()

    async def get_user_open_trades(self, user_id: int) -> List[FuturesTrade]:
        """Get all open trades for a user."""
        result = await self.session.execute(
            select(FuturesTrade).where(
                FuturesTrade.user_id == user_id,
                FuturesTrade.status == "open"
            ).order_by(FuturesTrade.opened_at.desc())
        )
        return list(result.scalars().all())

    async def get_user_closed_trades(self, user_id: int, limit: int = 20) -> List[FuturesTrade]:
        """Get closed trades for a user."""
        result = await self.session.execute(
            select(FuturesTrade).where(
                FuturesTrade.user_id == user_id,
                FuturesTrade.status.in_(["closed", "liquidated"])
            ).order_by(FuturesTrade.closed_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_user_all_trades(self, user_id: int) -> List[FuturesTrade]:
        """Get all trades for a user."""
        result = await self.session.execute(
            select(FuturesTrade).where(
                FuturesTrade.user_id == user_id
            ).order_by(FuturesTrade.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_high_risk_trades(self, user_id: int) -> List[FuturesTrade]:
        """Get open trades with high or extreme risk."""
        result = await self.session.execute(
            select(FuturesTrade).where(
                FuturesTrade.user_id == user_id,
                FuturesTrade.status == "open",
                FuturesTrade.risk_level.in_(["high", "extreme"])
            ).order_by(FuturesTrade.leverage.desc())
        )
        return list(result.scalars().all())

    async def update_trade(self, trade_id: int, **kwargs) -> Optional[FuturesTrade]:
        """Update trade fields."""
        trade = await self.get_by_id(trade_id)
        if trade:
            for key, value in kwargs.items():
                if hasattr(trade, key):
                    setattr(trade, key, value)
            await self.session.flush()
        return trade

    async def update_current_price(self, trade_id: int, current_price: float) -> Optional[FuturesTrade]:
        """Update trade's current price."""
        return await self.update_trade(trade_id, current_price=current_price)

    async def close_trade(
        self,
        trade_id: int,
        close_price: float,
        status: str = "closed"
    ) -> Optional[FuturesTrade]:
        """Close a trade and calculate P&L."""
        trade = await self.get_by_id(trade_id)
        if not trade or trade.status != "open":
            return None
        
        # Calculate P&L
        price_diff = close_price - trade.entry_price
        if trade.side == "short":
            price_diff = -price_diff
        
        pnl = price_diff * trade.quantity * trade.leverage
        pnl_percent = (price_diff / trade.entry_price) * 100 * trade.leverage if trade.entry_price > 0 else 0
        
        trade.pnl = pnl
        trade.pnl_percent = pnl_percent
        trade.current_price = close_price
        trade.status = status
        trade.closed_at = datetime.utcnow()
        
        await self.session.flush()
        return trade

    async def delete_trade(self, trade_id: int) -> bool:
        """Delete a trade."""
        trade = await self.get_by_id(trade_id)
        if trade:
            await self.session.delete(trade)
            await self.session.flush()
            return True
        return False

    async def get_user_stats(self, user_id: int) -> dict:
        """Get user's futures trading statistics."""
        open_trades = await self.get_user_open_trades(user_id)
        closed_trades = await self.get_user_closed_trades(user_id, limit=100)
        
        # Calculate stats
        total_margin = sum(t.margin for t in open_trades)
        unrealized_pnl = sum(t.unrealized_pnl or 0 for t in open_trades)
        realized_pnl = sum(t.pnl or 0 for t in closed_trades)
        
        winning_trades = [t for t in closed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl and t.pnl < 0]
        
        win_rate = len(winning_trades) / len(closed_trades) * 100 if closed_trades else 0
        
        # Calculate total risk from open positions
        total_risk_usd = sum(t.risk_usd or 0 for t in open_trades)
        
        return {
            "open_count": len(open_trades),
            "closed_count": len(closed_trades),
            "total_margin": total_margin,
            "unrealized_pnl": unrealized_pnl,
            "realized_pnl": realized_pnl,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": win_rate,
            "total_risk_usd": total_risk_usd
        }

    async def get_total_open_risk(self, user_id: int) -> float:
        """Get total risk in USDT from all open positions."""
        open_trades = await self.get_user_open_trades(user_id)
        return sum(t.risk_usd or 0 for t in open_trades)

    async def create_with_risk(
        self,
        user_id: int,
        pair: str,
        side: str,
        leverage: int,
        entry_price: float,
        quantity: float,
        margin: float,
        stop_loss: float,
        stop_percent: float,
        risk_usd: float,
        timeframe: str,
        zone_used: str = "management",
        take_profit: Optional[float] = None,
        notes: Optional[str] = None,
        target_1_price: Optional[float] = None,
        target_1_percent: Optional[float] = None,
        target_2_price: Optional[float] = None,
        target_2_percent: Optional[float] = None,
        target_3_price: Optional[float] = None,
        target_3_percent: Optional[float] = None,
        allocation_percent: Optional[float] = None
    ) -> FuturesTrade:
        """Create a new futures trade with risk management data."""
        pair = pair.upper().replace("/", "").replace("-", "")
        
        is_altcoin = self._is_altcoin(pair)
        risk_level = self._calculate_risk_level(leverage, is_altcoin)
        
        trade = FuturesTrade(
            user_id=user_id,
            pair=pair,
            side=side.lower(),
            leverage=leverage,
            entry_price=entry_price,
            quantity=quantity,
            margin=margin,
            stop_loss=stop_loss,
            stop_percent=stop_percent,
            risk_usd=risk_usd,
            timeframe=timeframe,
            zone_used=zone_used,
            take_profit=take_profit,
            current_price=entry_price,
            is_altcoin=is_altcoin,
            risk_level=risk_level,
            notes=notes,
            status="open",
            target_1_price=target_1_price,
            target_1_percent=target_1_percent,
            target_2_price=target_2_price,
            target_2_percent=target_2_percent,
            target_3_price=target_3_price,
            target_3_percent=target_3_percent,
            allocation_percent=allocation_percent
        )
        self.session.add(trade)
        await self.session.flush()
        return trade
