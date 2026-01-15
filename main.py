"""
Crypto Portfolio Bot - Main Entry Point

A Telegram bot for managing cryptocurrency portfolios with OKX integration.
Features:
- Track crypto assets with purchase prices and multiple entries
- Automatic alerts for 30%+ price drops (averaging down opportunity)
- Automatic alerts for 100%+ gains (partial sell recommendation)
- Death Cross detection (MA50 crosses below MA200)
- USDT reserve management (target 15%)
- Integration with OKX API for real-time prices
"""
import asyncio
import signal
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.bot import CryptoPortfolioBot
from src.services.price_monitor import PriceMonitor
from src.config import settings
from src.utils import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


class Application:
    """Main application class."""

    def __init__(self):
        self.bot = CryptoPortfolioBot()
        self.scheduler = AsyncIOScheduler()
        self.price_monitor: PriceMonitor = None
        self._shutdown_event = asyncio.Event()

    async def initialize(self):
        """Initialize all components."""
        logger.info("Initializing Crypto Portfolio Bot...")
        
        # Initialize bot
        await self.bot.initialize()
        
        # Initialize price monitor with bot instance
        self.price_monitor = PriceMonitor(bot=self.bot.application.bot)
        
        # Setup scheduled jobs
        self._setup_scheduler()
        
        logger.info("Application initialized successfully")

    def _setup_scheduler(self):
        """Setup scheduled jobs."""
        # Add price check job
        interval_minutes = settings.monitoring.check_interval_minutes
        
        self.scheduler.add_job(
            self._scheduled_price_check,
            'interval',
            minutes=interval_minutes,
            id='price_check',
            name='Price Check Job',
            replace_existing=True
        )
        
        logger.info(f"Price check scheduled every {interval_minutes} minutes")

    async def _scheduled_price_check(self):
        """Scheduled price check task."""
        logger.info("Running scheduled price check...")
        try:
            await self.price_monitor.check_all_assets()
        except Exception as e:
            logger.error(f"Error in scheduled price check: {e}")

    async def run(self):
        """Run the application."""
        try:
            await self.initialize()
            
            # Start scheduler
            self.scheduler.start()
            logger.info("Scheduler started")
            
            # Run initial price check
            asyncio.create_task(self._scheduled_price_check())
            
            # Run bot
            await self.bot.run()
            
            # Keep running until shutdown
            logger.info("Bot is running. Press Ctrl+C to stop.")
            await self._shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Application error: {e}")
            raise
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Shutdown the application."""
        logger.info("Shutting down application...")
        
        # Stop scheduler
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")
        
        # Close price monitor
        if self.price_monitor:
            await self.price_monitor.close()
            logger.info("Price monitor closed")
        
        # Stop bot
        await self.bot.stop()
        
        logger.info("Application shutdown complete")

    def request_shutdown(self):
        """Request application shutdown."""
        self._shutdown_event.set()


async def main():
    """Main entry point."""
    app = Application()
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        app.request_shutdown()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await app.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
