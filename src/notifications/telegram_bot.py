"""Telegram bot for notifications"""
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from typing import Optional

from ..utils.config import Config
from ..utils.logger import setup_logger
from .message_formatter import MessageFormatter

logger = setup_logger(__name__)


class TelegramNotifier:
    """Handles Telegram notifications"""

    def __init__(self):
        """Initialize Telegram bot"""
        if not Config.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not configured")

        if not Config.TELEGRAM_CHAT_ID:
            raise ValueError("TELEGRAM_CHAT_ID not configured")

        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.formatter = MessageFormatter()

        logger.info("Telegram notifier initialized")

    async def send_message(
        self,
        message: str,
        parse_mode: str = "HTML",
        disable_notification: bool = False
    ) -> Optional[int]:
        """
        Send message to Telegram

        Args:
            message: Message text
            parse_mode: Parse mode (HTML or Markdown)
            disable_notification: Whether to send silently

        Returns:
            Message ID if successful, None otherwise
        """
        # Test mode: just log the message
        if self.chat_id == "allow":
            logger.info("=" * 60)
            logger.info("📱 TELEGRAM MESSAGE (Test Mode):")
            logger.info("=" * 60)
            logger.info(message)
            logger.info("=" * 60)
            return 999999  # Fake message ID for test mode

        try:
            result = await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_notification=disable_notification
            )

            logger.info(f"Message sent successfully to {self.chat_id}")
            return result.message_id

        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return None

    async def send_value_bet_alert(
        self,
        fixture: dict,
        analysis: dict,
        value_bet: dict
    ) -> Optional[int]:
        """
        Send value bet alert

        Args:
            fixture: Fixture data
            analysis: Statistical analysis
            value_bet: Value bet data

        Returns:
            Message ID if successful
        """
        message = self.formatter.format_value_bet_alert(
            fixture=fixture,
            analysis=analysis,
            value_bet=value_bet
        )

        return await self.send_message(message)

    async def send_daily_summary(
        self,
        opportunities_count: int,
        best_value: dict = None
    ) -> Optional[int]:
        """
        Send daily summary

        Args:
            opportunities_count: Number of opportunities
            best_value: Best opportunity data

        Returns:
            Message ID if successful
        """
        message = self.formatter.format_daily_summary(
            opportunities_count=opportunities_count,
            best_value=best_value
        )

        return await self.send_message(message)

    async def send_startup_message(self) -> Optional[int]:
        """Send bot startup message"""
        message = self.formatter.format_startup_message()
        return await self.send_message(message, disable_notification=True)

    async def send_error_message(self, error: str) -> Optional[int]:
        """
        Send error message

        Args:
            error: Error description

        Returns:
            Message ID if successful
        """
        message = self.formatter.format_error_message(error)
        return await self.send_message(message)

    def send_message_sync(self, message: str) -> Optional[int]:
        """
        Send message synchronously (blocking)

        Args:
            message: Message text

        Returns:
            Message ID if successful
        """
        try:
            # Create new event loop if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(
                self.send_message(message)
            )

        except Exception as e:
            logger.error(f"Failed to send sync message: {e}")
            return None

    async def test_connection(self) -> bool:
        """
        Test Telegram bot connection

        Returns:
            True if connection successful
        """
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"Connected to Telegram bot: @{bot_info.username}")
            return True

        except TelegramError as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            return False
