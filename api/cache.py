"""Simple in-memory TTL cache for API responses."""

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import Any

_cache: dict[str, tuple[float, Any]] = {}
TTL = 60


def cached(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Cache function results for TTL seconds, keyed by function name + args."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        key = f"{fn.__module__}.{fn.__qualname__}:{args}:{kwargs}"
        now = time.time()
        if key in _cache and now - _cache[key][0] < TTL:
            return _cache[key][1]
        result = fn(*args, **kwargs)
        _cache[key] = (now, result)
        return result

    return wrapper
