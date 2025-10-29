"""Simple in-memory cache for API responses"""
from datetime import datetime, timedelta
from typing import Any, Optional
import threading

from .logger import setup_logger

logger = setup_logger(__name__)


class SimpleCache:
    """Thread-safe in-memory cache with TTL"""

    def __init__(self):
        """Initialize cache"""
        self._cache = {}
        self._lock = threading.Lock()
        logger.info("Simple cache initialized")

    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/not found
        """
        with self._lock:
            if key not in self._cache:
                return None

            item = self._cache[key]
            expires_at = item["expires_at"]

            # Check if expired
            if datetime.now() > expires_at:
                del self._cache[key]
                logger.debug(f"Cache expired: {key}")
                return None

            logger.debug(f"Cache hit: {key}")
            return item["value"]

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """
        Set item in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default 5 minutes)
        """
        with self._lock:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at
            }
            logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")

    def clear(self):
        """Clear all cache"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared ({count} items)")

    def remove(self, key: str):
        """Remove specific key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache removed: {key}")


# Global cache instance
fixtures_cache = SimpleCache()
