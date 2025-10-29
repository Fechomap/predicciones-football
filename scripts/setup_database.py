"""Database setup script"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import db_manager
from src.utils.config import Config
from src.utils.logger import logger


def setup_database():
    """Initialize and setup database"""
    try:
        logger.info("Starting database setup...")

        # Validate configuration
        Config.validate()
        logger.info("Configuration validated")

        # Initialize database connection
        db_manager.initialize()
        logger.info("Database connection established")

        # Create all tables
        db_manager.create_tables()
        logger.info("Database tables created successfully")

        logger.info("✅ Database setup completed successfully!")

    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    setup_database()
