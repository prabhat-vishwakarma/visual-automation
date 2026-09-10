"""Operational metrics.

Version 1 emits metrics as structured JSON log lines (see architecture doc
section 31). A Prometheus exporter is deliberately out of scope.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from typing import Any

from app.telemetry.logger import _RUN_ID


class Metrics:
    def __init__(self) -> None:
        self.counters: dict[str, int] = {}
        self.latencies: dict[str, list[float]] = {}

    def increment(self, name: str) -> None:
        self.counters[name] = self.counters.get(name, 0) + 1

    def record_latency(self, name: str, seconds: float) -> None:
        self.latencies.setdefault(name, []).append(seconds)

    def _metric(self, name: str, value: Any, mtype: str) -> str:
        return json.dumps(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "run_id": _RUN_ID.get(),
                "metric": name,
                "type": mtype,
                "value": value,
            },
            default=str,
        )

    def _line(self, name: str, value: Any, mtype: str = "counter") -> None:
        print(self._metric(name, value, mtype), file=sys.stderr, flush=True)

    def flush(self) -> None:
        for name, value in sorted(self.counters.items()):
            self._line(name, value, "counter")
        for name, latencies in sorted(self.latencies.items()):
            if latencies:
                self._line(name, sum(latencies) / len(latencies), "gauge")