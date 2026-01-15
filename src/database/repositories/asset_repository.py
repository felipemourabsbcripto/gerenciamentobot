"""
Repository for Asset model database operations.
"""
from typing import Optional, List
from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Asset


class AssetRepository:
    """Repository for Asset database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, coin_id: str, symbol: str,
                     name: str, quantity: float, purchase_price: float,
                     is_confirmed: bool = False) -> Asset:
        """Create a new asset."""
        total_invested = quantity * purchase_price
        asset = Asset(
            user_id=user_id,
            coin_id=coin_id,
            symbol=symbol.upper(),
            name=name,
            quantity=quantity,
            purchase_price=purchase_price,
            average_price=purchase_price,
            total_invested=total_invested,
            is_confirmed=is_confirmed
        )
        self.session.add(asset)
        await self.session.flush()
        return asset

    async def get_by_id(self, asset_id: int) -> Optional[Asset]:
        """Get asset by ID."""
        result = await self.session.execute(
            select(Asset).where(Asset.id == asset_id)
        )
        return result.scalar_one_or_none()

    async def get_user_assets(self, user_id: int) -> List[Asset]:
        """Get all active assets for a user."""
        result = await self.session.execute(
            select(Asset).where(
                Asset.user_id == user_id,
                Asset.is_active == True
            ).order_by(Asset.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_user_confirmed_assets(self, user_id: int) -> List[Asset]:
        """Get all confirmed assets for a user."""
        result = await self.session.execute(
            select(Asset).where(
                Asset.user_id == user_id,
                Asset.is_active == True,
                Asset.is_confirmed == True
            ).order_by(Asset.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_user_asset_by_coin(self, user_id: int, coin_id: str) -> Optional[Asset]:
        """Get user's asset by coin ID."""
        result = await self.session.execute(
            select(Asset).where(
                Asset.user_id == user_id,
                Asset.coin_id == coin_id,
                Asset.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def get_user_asset_by_symbol(self, user_id: int, symbol: str) -> Optional[Asset]:
        """Get user's asset by symbol."""
        result = await self.session.execute(
            select(Asset).where(
                Asset.user_id == user_id,
                Asset.symbol == symbol.upper(),
                Asset.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def update_asset(self, asset_id: int, **kwargs) -> Optional[Asset]:
        """Update asset fields."""
        asset = await self.get_by_id(asset_id)
        if asset:
            for key, value in kwargs.items():
                if hasattr(asset, key):
                    setattr(asset, key, value)
            await self.session.flush()
        return asset

    async def update_current_price(self, asset_id: int, current_price: float) -> Optional[Asset]:
        """Update asset's current price."""
        return await self.update_asset(asset_id, current_price=current_price)

    async def update_purchase_price(self, asset_id: int,
                                    new_quantity: float, new_purchase_price: float) -> Optional[Asset]:
        """Update asset purchase price (for averaging down)."""
        asset = await self.get_by_id(asset_id)
        if asset:
            # Calculate new average price
            old_total = asset.quantity * (asset.average_price or asset.purchase_price)
            new_total = new_quantity * new_purchase_price
            combined_quantity = asset.quantity + new_quantity
            
            asset.average_price = (old_total + new_total) / combined_quantity
            asset.quantity = combined_quantity
            asset.total_invested += new_total
            asset.times_averaged += 1
            await self.session.flush()
        return asset

    async def record_partial_sell(self, asset_id: int, 
                                   sell_quantity: float, sell_price: float) -> Optional[Asset]:
        """Record a partial sell and update quantities."""
        asset = await self.get_by_id(asset_id)
        if asset:
            asset.quantity -= sell_quantity
            asset.times_sold_partial += 1
            asset.last_alert_price = sell_price
            await self.session.flush()
        return asset

    async def update_alert_price(self, asset_id: int, alert_price: float) -> Optional[Asset]:
        """Update the last alert price for an asset."""
        return await self.update_asset(asset_id, last_alert_price=alert_price)

    async def update_death_cross(self, asset_id: int, has_death_cross: bool) -> Optional[Asset]:
        """Update death cross status for an asset."""
        from datetime import datetime
        return await self.update_asset(
            asset_id, 
            has_death_cross=has_death_cross,
            last_death_cross_alert=datetime.utcnow() if has_death_cross else None
        )

    async def delete_asset(self, asset_id: int) -> bool:
        """Soft delete an asset."""
        asset = await self.get_by_id(asset_id)
        if asset:
            asset.is_active = False
            await self.session.flush()
            return True
        return False

    async def get_all_active_assets(self) -> List[Asset]:
        """Get all active assets from all users."""
        result = await self.session.execute(
            select(Asset).where(Asset.is_active == True)
        )
        return list(result.scalars().all())

    async def get_assets_with_death_cross(self) -> List[Asset]:
        """Get all assets currently in death cross."""
        result = await self.session.execute(
            select(Asset).where(
                Asset.is_active == True,
                Asset.has_death_cross == True
            )
        )
        return list(result.scalars().all())
