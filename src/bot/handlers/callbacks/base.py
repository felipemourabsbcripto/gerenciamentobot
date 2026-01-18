"""
Base utilities for callback handlers.

Provides common imports and helper functions used across all callback handlers.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest

from src.database import (
    get_async_session,
    UserRepository,
    AssetRepository,
    AlertRepository,
    EntryRepository,
)
from src.database.repositories import FuturesRepository, AdminRepository
from src.utils import KeyboardBuilder, MessageFormatter
from src.utils.logger import get_logger
from src.core.constants import MAJOR_COINS, STABLECOINS, TREND_EMOJIS, RISK_EMOJIS

logger = get_logger(__name__)


async def get_user_or_error(query, telegram_id: int):
    """
    Get user from database or send error message.
    
    Returns:
        User object if found, None otherwise (error message already sent)
    """
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado. Use /start para começar.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return None
        
        return user


async def safe_edit_message(query, text: str, reply_markup=None, parse_mode=ParseMode.MARKDOWN):
    """
    Safely edit a message, handling common errors.
    
    Args:
        query: Callback query object
        text: New message text
        reply_markup: Optional keyboard markup
        parse_mode: Message parse mode
    """
    try:
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error editing message: {e}")
            raise


def get_pnl_emoji(value: float) -> str:
    """Get appropriate emoji for P&L value."""
    return "🟢" if value >= 0 else "🔴"


def get_trend_emoji(trend: str) -> str:
    """Get emoji for trend direction."""
    return TREND_EMOJIS.get(trend.lower(), "⚪")


def get_risk_emoji(risk_level: str) -> str:
    """Get emoji for risk level."""
    return RISK_EMOJIS.get(risk_level.lower(), "⚪")


def calculate_change_percent(current: float, original: float) -> float:
    """Calculate percentage change between two values."""
    if original <= 0:
        return 0.0
    return ((current - original) / original) * 100


def format_asset_button(asset) -> str:
    """Format asset information for inline button display."""
    change = ""
    if asset.current_price and asset.purchase_price:
        pct = calculate_change_percent(asset.current_price, asset.purchase_price)
        emoji = "🟢" if pct >= 0 else "🔴"
        change = f" {emoji} {pct:+.1f}%"
    
    price = asset.current_price or asset.purchase_price
    return f"{asset.symbol.upper()} - ${price:,.4f}{change}"
