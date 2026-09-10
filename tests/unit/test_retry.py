"""Unit tests for bounded retry helpers."""

import pytest

from app.workflow.retry import RetryCounter, bounded_retry


def test_retry_counter_bound():
    counter = RetryCounter(limit=2)
    assert counter.exhausted() is False
    assert counter.attempts == 0


def test_counter_exhausted_at_limit():
    counter = RetryCounter(limit=2)
    counter._count = 2
    assert counter.exhausted() is True


def test_bounded_retry_succeeds_after_failures():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("not yet")
        return "ok"

    result = bounded_retry(3, flaky)
    assert result == "ok"
    assert calls["n"] == 3


def test_bounded_retry_raises_when_exhausted():
    calls = {"n": 0}

    def always_fails():
        calls["n"] += 1
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        bounded_retry(1, always_fails)
    assert calls["n"] == 2


def test_rejects_negative_limit():
    with pytest.raises(ValueError):
        RetryCounter(limit=-1)