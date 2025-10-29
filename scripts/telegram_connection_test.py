"""Test Telegram bot connection"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.notifications import TelegramNotifier
from src.utils.config import Config
from src.utils.logger import logger


async def test_telegram():
    """Test Telegram bot"""
    try:
        logger.info("Testing Telegram bot connection...")

        # Validate config
        Config.validate()

        # Create notifier
        notifier = TelegramNotifier()

        # Test connection
        connected = await notifier.test_connection()

        if connected:
            logger.info("✅ Telegram bot connected successfully!")

            # Send test message
            logger.info("Sending test message...")
            message_id = await notifier.send_startup_message()

            if message_id:
                logger.info(f"✅ Test message sent successfully! (ID: {message_id})")
            else:
                logger.error("❌ Failed to send test message")

        else:
            logger.error("❌ Failed to connect to Telegram bot")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_telegram())
