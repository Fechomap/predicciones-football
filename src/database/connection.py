"""Database connection management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator

from .models import Base
from ..utils.logger import setup_logger
from ..utils.config import Config

logger = setup_logger(__name__)


class DatabaseManager:
    """Manages database connections and sessions"""

    def __init__(self):
        """Initialize database manager"""
        self.engine = None
        self.SessionLocal = None

    def initialize(self):
        """Initialize database connection"""
        if not Config.DATABASE_URL:
            raise ValueError("DATABASE_URL not configured")

        logger.info("Initializing database connection...")

        # Create engine with connection pooling
        self.engine = create_engine(
            Config.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            echo=False  # Set to True for SQL query logging
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        logger.info("Database connection initialized successfully")

    def create_tables(self):
        """Create all database tables"""
        if not self.engine:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        if not self.engine:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session with context manager

        Usage:
            with db_manager.get_session() as session:
                # Use session here
                pass
        """
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")


# Global database manager instance
db_manager = DatabaseManager()
