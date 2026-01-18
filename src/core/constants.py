"""
Centralized constants for the Crypto Portfolio Bot.

This module contains all constants used across the application,
avoiding duplication and making it easy to modify values in one place.
"""
from typing import Dict, Set, List

# =============================================================================
# CRYPTOCURRENCY CONSTANTS
# =============================================================================

# Major coins (not altcoins) - used for risk assessment
MAJOR_COINS: Set[str] = {"BTC", "ETH", "BNB"}

# Stablecoins for reserve calculations
STABLECOINS: Set[str] = {"USDT", "USDC", "BUSD", "DAI", "TUSD"}

# Quote currencies for pair parsing
QUOTE_CURRENCIES: List[str] = ["USDT", "USDC", "USD", "BTC", "ETH", "BNB", "BUSD"]


# =============================================================================
# TIMEFRAME CONSTANTS
# =============================================================================

VALID_TIMEFRAMES: List[str] = [
    "1m", "3m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1M"
]

RECOMMENDED_TIMEFRAMES: List[str] = ["4h", "1d"]


# =============================================================================
# RISK MANAGEMENT CONSTANTS
# =============================================================================

class RiskLevels:
    """Risk level thresholds and configurations."""
    
    # Leverage thresholds
    EXTREME_LEVERAGE: int = 20
    HIGH_LEVERAGE: int = 10
    MODERATE_LEVERAGE: int = 5
    SAFE_ALTCOIN_MAX: int = 3
    
    # Risk percentages
    DEFAULT_RISK_PERCENT: float = 5.0
    MIN_RISK_PERCENT: float = 0.5
    MAX_RISK_PERCENT: float = 20.0
    
    # Reserve targets
    DEFAULT_RESERVE_PERCENT: float = 15.0
    CRITICAL_RESERVE_THRESHOLD: float = 0.5  # 50% of target


RISK_LEVELS = RiskLevels()


class AlertThresholds:
    """Alert threshold configurations."""
    
    DROP_PERCENT: float = 30.0    # Alert when asset drops 30%+
    PROFIT_PERCENT: float = 100.0  # Alert when asset profits 100%+
    SELL_RECOMMENDATION_PERCENT: float = 50.0  # Recommend selling 50%
    
    # Death cross alert cooldown (hours)
    DEATH_CROSS_ALERT_COOLDOWN_HOURS: int = 24


ALERT_THRESHOLDS = AlertThresholds()


# =============================================================================
# EMOJI CONSTANTS
# =============================================================================

# Trend direction emojis
TREND_EMOJIS: Dict[str, str] = {
    "bullish": "🟢",
    "bearish": "🔴",
    "neutral": "⚪",
    "strong_bullish": "🟢🟢",
    "strong_bearish": "🔴🔴",
}

# Risk level emojis
RISK_EMOJIS: Dict[str, str] = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🟠",
    "extreme": "🔴",
    "critical": "💀",
}

# P&L emojis
PNL_EMOJIS: Dict[str, str] = {
    "profit": "🟢",
    "loss": "🔴",
    "neutral": "🔹",
}

# Trade side emojis
SIDE_EMOJIS: Dict[str, str] = {
    "long": "🟢",
    "short": "🔴",
}

# General status emojis
STATUS_EMOJIS: Dict[str, str] = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "loading": "⏳",
    "death_cross": "☠️",
    "golden_cross": "✨",
}


# =============================================================================
# FORMATTING CONSTANTS
# =============================================================================

class FormattingConfig:
    """Configuration for number and price formatting."""
    
    # Price decimal places by magnitude
    DECIMALS_LARGE: int = 2      # >= $1000
    DECIMALS_MEDIUM: int = 2     # >= $1
    DECIMALS_SMALL: int = 4      # >= $0.01
    DECIMALS_TINY: int = 6       # >= $0.0001
    DECIMALS_MICRO: int = 8      # < $0.0001
    
    # Thresholds
    THRESHOLD_LARGE: float = 1000.0
    THRESHOLD_MEDIUM: float = 1.0
    THRESHOLD_SMALL: float = 0.01
    THRESHOLD_TINY: float = 0.0001


FORMATTING_CONFIG = FormattingConfig()


# =============================================================================
# PAGINATION CONSTANTS
# =============================================================================

class PaginationConfig:
    """Pagination settings for lists."""
    
    USERS_PER_PAGE: int = 10
    TRADES_PER_PAGE: int = 10
    ASSETS_PER_PAGE: int = 15
    ALERTS_PER_PAGE: int = 10
    LOGS_PER_PAGE: int = 20


PAGINATION_CONFIG = PaginationConfig()


# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

class ValidationConfig:
    """Input validation configurations."""
    
    # Leverage limits
    MIN_LEVERAGE: int = 1
    MAX_LEVERAGE: int = 125
    
    # Name validation
    MIN_NAME_LENGTH: int = 3
    
    # Phone validation
    MIN_PHONE_LENGTH: int = 10
    
    # Targets
    MAX_TARGETS: int = 3


VALIDATION_CONFIG = ValidationConfig()
