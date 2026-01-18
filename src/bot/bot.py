"""
Main Telegram bot class.
"""
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from src.config import settings
from src.database import db
from src.bot.handlers import (
    start_command,
    menu_command,
    portfolio_command,
    help_command,
    callback_handler,
    message_handler,
    # Gorni Strategies
    estrategias_command,
    estrategias_callback,
)
from src.utils import KeyboardBuilder
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CryptoPortfolioBot:
    """Main Telegram bot class."""

    def __init__(self):
        self.token = settings.telegram.bot_token
        self.application: Application = None
        self.bot: Bot = None

    async def initialize(self):
        """Initialize the bot and database."""
        # Initialize database
        await db.init_db()
        logger.info("Database initialized")

        # Build application
        self.application = (
            Application.builder()
            .token(self.token)
            .build()
        )
        self.bot = self.application.bot

        # Register handlers
        self._register_handlers()
        
        logger.info("Bot initialized successfully")

    def _register_handlers(self):
        """Register all bot handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("menu", menu_command))
        self.application.add_handler(CommandHandler("portfolio", portfolio_command))
        self.application.add_handler(CommandHandler("help", help_command))
        
        # Gorni Strategies command
        self.application.add_handler(CommandHandler("estrategias", estrategias_command))

        # Gorni Strategies callback handler (isolado com pattern gg_*)
        # IMPORTANTE: Deve vir ANTES do callback_handler geral
        self.application.add_handler(CallbackQueryHandler(estrategias_callback, pattern="^gg_"))
        
        # Callback query handler geral (para todos os outros callbacks)
        self.application.add_handler(CallbackQueryHandler(callback_handler))

        # Message handler (for user input)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
        )

        # Error handler
        self.application.add_error_handler(self._error_handler)

        logger.info("All handlers registered (including Gorni Strategies)")

    async def _error_handler(self, update: Update, context):
        """Handle errors."""
        logger.error(f"Error handling update {update}: {context.error}")
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Ocorreu um erro. Por favor, tente novamente.",
                    reply_markup=KeyboardBuilder.back_to_menu()
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")

    async def send_notification(self, telegram_id: int, message: str, 
                                alert_type: str = None, asset_id: int = None):
        """Send a notification to a user."""
        try:
            keyboard = None
            if alert_type and asset_id:
                keyboard = KeyboardBuilder.alert_response(alert_type, asset_id)
            
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            logger.info(f"Notification sent to user {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification to {telegram_id}: {e}")
            return False

    async def run(self):
        """Run the bot using polling."""
        logger.info("Starting bot polling...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
        logger.info("Bot is now running and listening for updates...")

    async def stop(self):
        """Stop the bot."""
        logger.info("Stopping bot...")
        if self.application:
            if self.application.updater.running:
                await self.application.updater.stop()
            if self.application.running:
                await self.application.stop()
                await self.application.shutdown()
        await db.close()
        logger.info("Bot stopped")
