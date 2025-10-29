"""
Football Betting Analytics Bot
Main entry point
"""
import asyncio
import signal
import sys

from src.database import db_manager
from src.services import BotService, BotScheduler
from src.notifications import TelegramNotifier, TelegramCommandBot
from src.utils.config import Config
from src.utils.logger import logger


class FootballBettingBot:
    """Main bot application"""

    def __init__(self):
        """Initialize bot"""
        self.bot_service = None
        self.scheduler = None
        self.telegram = None
        self.command_bot = None
        self.running = False

    async def startup(self):
        """Startup sequence"""
        try:
            logger.info("=" * 60)
            logger.info("⚽ Football Betting Analytics Bot")
            logger.info("=" * 60)

            # Configuration is automatically validated by Pydantic on import
            logger.info("✅ Configuration validated")

            # Initialize database
            logger.info("Initializing database...")
            db_manager.initialize()
            logger.info("✅ Database connected")

            # Create tables if needed
            db_manager.create_tables()
            logger.info("✅ Database tables ready")

            # Initialize services
            logger.info("Initializing services...")
            self.bot_service = BotService()
            self.telegram = TelegramNotifier()
            logger.info("✅ Services initialized")

            # Test Telegram connection
            logger.info("Testing Telegram connection...")
            telegram_ok = await self.telegram.test_connection()
            if not telegram_ok:
                raise Exception("Failed to connect to Telegram")
            logger.info("✅ Telegram connected")

            # Sync leagues
            logger.info("Syncing leagues...")
            self.bot_service.sync_leagues()
            logger.info("✅ Leagues synced")

            # Initialize scheduler
            logger.info("Starting scheduler...")
            self.scheduler = BotScheduler(self.bot_service)
            self.scheduler.start()
            logger.info("✅ Scheduler started")

            # Send startup notification
            await self.telegram.send_startup_message()
            logger.info("✅ Startup notification sent")

            # Initialize command bot
            logger.info("Starting command bot...")
            self.command_bot = TelegramCommandBot(self.bot_service)
            await self.command_bot.start()
            logger.info("✅ Command bot started")

            # Run initial fixture check
            logger.info("Running initial fixture check...")
            await self.bot_service.check_fixtures()
            logger.info("✅ Initial check completed")

            self.running = True
            logger.info("=" * 60)
            logger.info("🚀 Bot is now running!")
            logger.info("=" * 60)
            logger.info("📱 Telegram commands ready: /start, /status, /partidos, /ligas, /help")
            logger.info(f"Monitoring leagues: {Config.ENABLED_LEAGUES}")
            logger.info(f"Alert time: {Config.ALERT_TIME_MINUTES} minutes before kickoff")
            logger.info(f"Check interval: {Config.CHECK_INTERVAL} minutes")
            logger.info(f"Minimum edge: {Config.MINIMUM_EDGE * 100}%")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ Startup failed: {e}")
            raise

    async def shutdown(self):
        """Shutdown sequence"""
        logger.info("Shutting down bot...")

        self.running = False

        # Stop command bot
        if self.command_bot:
            await self.command_bot.stop()
            logger.info("Command bot stopped")

        # Stop scheduler
        if self.scheduler:
            self.scheduler.stop()
            logger.info("Scheduler stopped")

        # Close database
        if db_manager:
            db_manager.close()
            logger.info("Database connection closed")

        logger.info("Bot shut down successfully")

    async def run(self):
        """Main run loop"""
        try:
            await self.startup()

            # Keep running
            while self.running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            if self.telegram:
                await self.telegram.send_error_message(str(e))
        finally:
            await self.shutdown()


def signal_handler(sig, frame):
    """Handle interrupt signals"""
    logger.info("Received signal to stop")
    sys.exit(0)


def main():
    """Main entry point"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and run bot
    bot = FootballBettingBot()

    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
