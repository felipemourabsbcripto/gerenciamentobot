"""
Core module - Centralized constants, types, enums and base utilities.

This module provides:
- Constants: MAJOR_COINS, STABLECOINS, VALID_TIMEFRAMES, etc.
- Enums: TradeSide, RiskLevel, AlertType, etc.
- Messages: Centralized message templates for i18n

Usage:
    from src.core import MAJOR_COINS, TradeSide, MSG
"""
from .constants import (
    MAJOR_COINS,
    STABLECOINS,
    VALID_TIMEFRAMES,
    RISK_LEVELS,
    ALERT_THRESHOLDS,
    TREND_EMOJIS,
    RISK_EMOJIS,
    PNL_EMOJIS,
    SIDE_EMOJIS,
    STATUS_EMOJIS,
    FORMATTING_CONFIG,
    PAGINATION_CONFIG,
    VALIDATION_CONFIG,
)
from .enums import (
    TradeSide,
    RiskLevel,
    AlertType,
    RegistrationStep,
    UserState,
    FuturesState,
    TradeStatus,
    TrendDirection,
)
from .messages import MSG, Messages

__all__ = [
    # Constants
    "MAJOR_COINS",
    "STABLECOINS", 
    "VALID_TIMEFRAMES",
    "RISK_LEVELS",
    "ALERT_THRESHOLDS",
    "TREND_EMOJIS",
    "RISK_EMOJIS",
    "PNL_EMOJIS",
    "SIDE_EMOJIS",
    "STATUS_EMOJIS",
    "FORMATTING_CONFIG",
    "PAGINATION_CONFIG",
    "VALIDATION_CONFIG",
    # Enums
    "TradeSide",
    "RiskLevel",
    "AlertType",
    "RegistrationStep",
    "UserState",
    "FuturesState",
    "TradeStatus",
    "TrendDirection",
    # Messages
    "MSG",
    "Messages",
]
