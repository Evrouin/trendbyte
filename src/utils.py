"""Shared exceptions and retry utilities."""

from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from src.infra.logger import Logger

logger = Logger.get(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class CollectorError(Exception):
    """Raised when a data source fails."""


class RateLimitError(CollectorError):
    """Raised when API rate limit is hit."""


def retry(max_attempts: int = 3, backoff: float = 2.0) -> Callable[[F], F]:
    """Retry decorator with exponential backoff for rate limits."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    if attempt == max_attempts - 1:
                        raise
                    wait = backoff**attempt
                    logger.warning(
                        "Rate limited, retrying in %.1fs",
                        wait,
                        extra={"attempt": attempt + 1, "error": str(e)},
                    )
                    time.sleep(wait)

        return wrapper  # type: ignore[return-value]

    return decorator
