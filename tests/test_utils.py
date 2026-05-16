"""Tests for retry utility."""

import pytest

from src.utils import RateLimitError, retry


def test_retry_succeeds_on_first_attempt() -> None:
    call_count = 0

    @retry(max_attempts=3, backoff=0.01)
    def succeed() -> str:
        nonlocal call_count
        call_count += 1
        return "ok"

    assert succeed() == "ok"
    assert call_count == 1


def test_retry_recovers_after_failure() -> None:
    call_count = 0

    @retry(max_attempts=3, backoff=0.01)
    def fail_then_succeed() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RateLimitError("rate limited")
        return "ok"

    assert fail_then_succeed() == "ok"
    assert call_count == 3


def test_retry_raises_after_max_attempts() -> None:
    @retry(max_attempts=2, backoff=0.01)
    def always_fail() -> str:
        raise RateLimitError("rate limited")

    with pytest.raises(RateLimitError):
        always_fail()
