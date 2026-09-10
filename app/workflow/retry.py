"""Bounded retry helpers. No retry is ever unbounded."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class RetryCounter:
    """A simple bounded attempt counter."""

    def __init__(self, limit: int) -> None:
        if limit < 0:
            raise ValueError("retry limit must be >= 0")
        self.limit = limit
        self._count = 0

    @property
    def attempts(self) -> int:
        return self._count

    def exhausted(self) -> bool:
        return self._count >= self.limit


def bounded_retry(
    n: int,
    func: Callable[[], T],
    on_retry: Callable[[int], None] | None = None,
) -> T:
    """Run func up to n+1 times; re-raise the last exception if all fail."""
    for attempt in range(n + 1):
        try:
            return func()
        except Exception:
            if attempt >= n:
                raise
            if on_retry is not None:
                on_retry(attempt + 1)
    raise RuntimeError("unreachable")  # pragma: no cover