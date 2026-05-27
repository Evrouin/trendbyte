from __future__ import annotations

import time
from collections.abc import Callable
from enum import Enum
from typing import Any


class State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = State.CLOSED
        self.failures = 0
        self.last_failure_time: float = 0

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if self.state == State.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = State.HALF_OPEN
            else:
                return None

        try:
            result = fn(*args, **kwargs)
            if self.state == State.HALF_OPEN:
                self.state = State.CLOSED
                self.failures = 0
            return result
        except Exception:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.state == State.HALF_OPEN or self.failures >= self.failure_threshold:
                self.state = State.OPEN
            return None
