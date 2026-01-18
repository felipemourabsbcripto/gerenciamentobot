"""
Enumerations for the Crypto Portfolio Bot.

These enums provide type-safe constants for common values.
"""
from enum import Enum, auto


class TradeSide(str, Enum):
    """Trade direction/side."""
    LONG = "long"
    SHORT = "short"
    
    @property
    def emoji(self) -> str:
        """Get emoji for this trade side."""
        return "🟢" if self == TradeSide.LONG else "🔴"
    
    @property
    def display_name(self) -> str:
        """Get display name for this trade side."""
        return "LONG" if self == TradeSide.LONG else "SHORT"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"
    
    @property
    def emoji(self) -> str:
        """Get emoji for this risk level."""
        emojis = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🟠",
            RiskLevel.EXTREME: "💀",
        }
        return emojis.get(self, "⚪")


class AlertType(str, Enum):
    """Types of alerts."""
    DROP = "drop"
    PROFIT = "profit"
    DEATH_CROSS = "death_cross"
    GOLDEN_CROSS = "golden_cross"
    RESERVE_LOW = "reserve_low"
    LIQUIDATION_WARNING = "liquidation_warning"


class RegistrationStep(str, Enum):
    """User registration flow steps."""
    NAME = "name"
    PHONE = "phone"
    BIRTH_DATE = "birth_date"
    FUTURES_BALANCE = "futures_balance"
    TERMS = "terms"
    COMPLETE = "complete"


class UserState(str, Enum):
    """User interaction states for message handling."""
    IDLE = "idle"
    
    # Coin/Asset states
    WAITING_COIN_SEARCH = "waiting_coin_search"
    SEARCHING_COIN = "searching_coin"
    WAITING_QUANTITY = "waiting_quantity"
    WAITING_PRICE = "waiting_price"
    WAITING_TOTAL_INVESTED = "waiting_total_invested"
    
    # Entry states
    WAITING_ENTRY_QUANTITY = "waiting_entry_quantity"
    WAITING_ENTRY_PRICE = "waiting_entry_price"
    
    # Sell states
    WAITING_SELL_QUANTITY = "waiting_sell_quantity"
    WAITING_SELL_PRICE = "waiting_sell_price"
    
    # Settings states
    WAITING_RESERVE_TARGET = "waiting_reserve_target"


class FuturesState(str, Enum):
    """Futures trade creation states."""
    AWAITING_PAIR = "awaiting_futures_pair"
    AWAITING_ENTRY = "awaiting_futures_entry"
    AWAITING_SIDE = "awaiting_futures_side"
    AWAITING_LEVERAGE = "awaiting_futures_leverage"
    AWAITING_CUSTOM_LEVERAGE = "awaiting_futures_custom_leverage"
    AWAITING_STOP_LOSS = "awaiting_futures_stop_loss"
    AWAITING_STOP_PERCENT = "awaiting_futures_stop_percent"
    AWAITING_TARGETS = "awaiting_futures_targets"
    AWAITING_TIMEFRAME = "awaiting_futures_timeframe"
    AWAITING_QUANTITY = "awaiting_futures_quantity"
    AWAITING_MARGIN = "awaiting_futures_margin"
    AWAITING_CLOSE_PRICE = "awaiting_futures_close_price"
    AWAITING_SLTP = "awaiting_futures_sltp"
    AWAITING_BALANCE = "awaiting_futures_balance"
    AWAITING_RISK_PERCENT = "awaiting_futures_risk_percent"


class TradeStatus(str, Enum):
    """Futures trade status."""
    OPEN = "open"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"


class TrendDirection(str, Enum):
    """Trend analysis direction."""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"
    
    @property
    def emoji(self) -> str:
        """Get emoji for trend direction."""
        emojis = {
            TrendDirection.STRONG_BULLISH: "🟢🟢",
            TrendDirection.BULLISH: "🟢",
            TrendDirection.NEUTRAL: "⚪",
            TrendDirection.BEARISH: "🔴",
            TrendDirection.STRONG_BEARISH: "🔴🔴",
        }
        return emojis.get(self, "⚪")
    
    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        names = {
            TrendDirection.STRONG_BULLISH: "Forte Alta",
            TrendDirection.BULLISH: "Alta",
            TrendDirection.NEUTRAL: "Neutro",
            TrendDirection.BEARISH: "Baixa",
            TrendDirection.STRONG_BEARISH: "Forte Baixa",
        }
        return names.get(self, "Desconhecido")
