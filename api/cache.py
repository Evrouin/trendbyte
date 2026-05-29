from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import Any

_cache: dict[str, tuple[float, Any]] = {}
TTL = 60
CONTENT_TTL = 300


def cached(fn: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        filtered_kwargs = {k: v for k, v in kwargs.items() if not hasattr(v, "execute")}
        key = f"{fn.__module__}.{fn.__qualname__}:{filtered_kwargs}"
        now = time.time()
        if key in _cache and now - _cache[key][0] < TTL:
            return _cache[key][1]
        result = await fn(*args, **kwargs)
        _cache[key] = (now, result)
        return result

    return wrapper


def cached_content(fn: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        key = f"{fn.__module__}.{fn.__qualname__}"
        now = time.time()
        if key in _cache and now - _cache[key][0] < CONTENT_TTL:
            return _cache[key][1]
        result = await fn(*args, **kwargs)
        _cache[key] = (now, result)
        return result

    return wrapper
