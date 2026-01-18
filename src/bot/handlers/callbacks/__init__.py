"""
Callback handlers package.

This module provides organized callback handling through:
- base.py: Shared utilities and helper functions

The callback_handler is re-exported from the main callbacks.py file
to maintain backward compatibility while we organize the code.
"""

# Re-export from original module
from src.bot.handlers.callbacks_original import callback_handler

# Export utilities
from .base import (
    get_user_or_error,
    safe_edit_message,
    get_pnl_emoji,
    get_trend_emoji,
    get_risk_emoji,
    calculate_change_percent,
    format_asset_button,
)

__all__ = [
    "callback_handler",
    "get_user_or_error",
    "safe_edit_message",
    "get_pnl_emoji",
    "get_trend_emoji",
    "get_risk_emoji",
    "calculate_change_percent",
    "format_asset_button",
]
