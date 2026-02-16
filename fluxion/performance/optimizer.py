"""Connection optimizer — adaptive concurrency scaling."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class _Sample:
    concurrency: int
    throughput: float
    timestamp: float


class ConnectionOptimizer:
    """Dynamically adjusts the number of parallel connections.

    Strategy:
    - Start with an initial concurrency.
    - Periodically measure aggregate throughput.
    - If throughput improves with more connections → scale up.
    - If throughput degrades or plateaus → scale down.
    - Detect server throttling (HTTP 429 / reduced throughput) and back off.
    """

    def __init__(
        self,
        initial: int = 4,
        minimum: int = 1,
        maximum: int = 32,
        probe_interval_sec: float = 2.0,
    ) -> None:
        self._concurrency = initial
        self._min = minimum
        self._max = maximum
        self._probe_interval = probe_interval_sec
        self._history: list[_Sample] = []
        self._last_probe = time.monotonic()
        self._throttle_count = 0

    @property
    def concurrency(self) -> int:
        return self._concurrency

    def report_throughput(self, throughput_bps: float) -> None:
        """Report observed aggregate throughput."""
        now = time.monotonic()
        self._history.append(_Sample(self._concurrency, throughput_bps, now))
        if len(self._history) > 100:
            self._history = self._history[-50:]

        if now - self._last_probe >= self._probe_interval:
            self._adapt()
            self._last_probe = now

    def report_throttle(self) -> None:
        """Report a server throttle signal (429, reduced throughput)."""
        self._throttle_count += 1
        # Aggressive back-off on throttle
        self._concurrency = max(self._min, self._concurrency // 2)

    def _adapt(self) -> None:
        if len(self._history) < 4:
            return

        recent = self._history[-4:]
        older = self._history[-8:-4] if len(self._history) >= 8 else self._history[:4]

        avg_recent = sum(s.throughput for s in recent) / len(recent)
        avg_older = sum(s.throughput for s in older) / len(older)

        if self._throttle_count > 0:
            self._throttle_count = max(0, self._throttle_count - 1)
            return  # Stay at reduced concurrency

        improvement = (avg_recent - avg_older) / max(avg_older, 1.0)
        if improvement > 0.05:
            # Throughput improved — try more connections
            self._concurrency = min(self._concurrency + 1, self._max)
        elif improvement < -0.1:
            # Throughput degraded — reduce
            self._concurrency = max(self._concurrency - 1, self._min)

    def suggest_concurrency(self, content_length: int | None) -> int:
        """Suggest an initial concurrency based on file size."""
        if content_length is None:
            return self._min
        mb = content_length / (1024 * 1024)
        if mb < 1:
            return 1
        if mb < 10:
            return min(4, self._max)
        if mb < 100:
            return min(8, self._max)
        return min(16, self._max)
