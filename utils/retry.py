from __future__ import annotations

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from playwright.async_api import TimeoutError as PlaywrightTimeout
from loguru import logger


def playwright_retry(attempts: int = 3, min_wait: int = 2, max_wait: int = 10):
    """Decorator for retrying Playwright operations."""
    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((PlaywrightTimeout, Exception)),
        before_sleep=lambda rs: logger.warning(
            f"Retry {rs.attempt_number}/{attempts} after error: {rs.outcome.exception()}"
        ),
        reraise=True,
    )
