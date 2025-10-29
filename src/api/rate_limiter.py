"""Rate limiter for API requests"""
import time
from collections import deque
from threading import Lock
from typing import Callable, Any

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class RateLimiter:
    """
    Rate limiter to control API request frequency

    Implements token bucket algorithm
    """

    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = Lock()

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator to rate limit function calls

        Usage:
            @rate_limiter
            def my_api_call():
                pass
        """
        def wrapper(*args, **kwargs) -> Any:
            self.wait_if_needed()
            return func(*args, **kwargs)
        return wrapper

    def wait_if_needed(self):
        """Wait if rate limit is exceeded"""
        with self.lock:
            now = time.time()

            # Remove old requests outside time window
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()

            # Check if we've hit the limit
            if len(self.requests) >= self.max_requests:
                sleep_time = self.time_window - (now - self.requests[0])
                if sleep_time > 0:
                    logger.warning(
                        f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds..."
                    )
                    time.sleep(sleep_time)

                    # Clean up old requests after sleeping
                    now = time.time()
                    while self.requests and self.requests[0] < now - self.time_window:
                        self.requests.popleft()

            # Add current request
            self.requests.append(now)

    def reset(self):
        """Reset rate limiter"""
        with self.lock:
            self.requests.clear()
            logger.info("Rate limiter reset")
