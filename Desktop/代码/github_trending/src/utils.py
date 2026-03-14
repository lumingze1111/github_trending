"""Utility functions for the GitHub Trending scraper."""

import time
import functools
from typing import List, Callable
from loguru import logger


# Retryable exception types
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def retry_on_exception(
    max_retries: int = 3,
    backoff: List[int] = None
) -> Callable:
    """
    Decorator that retries a function on retryable exceptions.

    Args:
        max_retries: Maximum number of retry attempts
        backoff: List of sleep durations between retries (seconds)

    Returns:
        Decorated function

    Raises:
        Original exception if all retries fail
    """
    if backoff is None:
        backoff = [1, 2, 4]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RETRYABLE_EXCEPTIONS as e:
                    if attempt == max_retries - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {e}"
                        )
                        raise

                    sleep_time = backoff[min(attempt, len(backoff) - 1)]
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {sleep_time}s..."
                    )
                    time.sleep(sleep_time)
                except Exception as e:
                    # Non-retryable exception, raise immediately
                    logger.error(f"{func.__name__} failed with non-retryable error: {e}")
                    raise

            return None  # Should never reach here

        return wrapper
    return decorator
