"""Bandwidth estimation — tracks transfer speeds with EMA smoothing."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass


@dataclass
class _SpeedSample:
    bytes_count: int
    elapsed: float
    timestamp: float


class BandwidthEstimator:
    """Estimates current and average bandwidth using a sliding window.

    Uses exponential moving average for smoothed speed reporting
    and a fixed-size window for percentile estimation.
    """

    def __init__(
        self,
        window_size: int = 30,
        ema_alpha: float = 0.3,
    ) -> None:
        self._window: deque[_SpeedSample] = deque(maxlen=window_size)
        self._alpha = ema_alpha
        self._ema_speed: float | None = None
        self._total_bytes = 0
        self._start_time: float | None = None

    def record(self, bytes_count: int, elapsed: float) -> None:
        """Record a completed transfer sample."""
        now = time.monotonic()
        if self._start_time is None:
            self._start_time = now

        sample = _SpeedSample(bytes_count, elapsed, now)
        self._window.append(sample)
        self._total_bytes += bytes_count

        speed = bytes_count / max(elapsed, 0.001)
        if self._ema_speed is None:
            self._ema_speed = speed
        else:
            self._ema_speed = self._alpha * speed + (1 - self._alpha) * self._ema_speed

    @property
    def current_speed(self) -> float:
        """Smoothed current speed in bytes/sec."""
        return self._ema_speed or 0.0

    @property
    def average_speed(self) -> float:
        """Overall average speed in bytes/sec."""
        if not self._start_time:
            return 0.0
        elapsed = time.monotonic() - self._start_time
        if elapsed <= 0:
            return 0.0
        return self._total_bytes / elapsed

    @property
    def total_bytes(self) -> int:
        return self._total_bytes

    def eta_seconds(self, remaining_bytes: int) -> float | None:
        """Estimate seconds until *remaining_bytes* finishes."""
        speed = self.current_speed
        if speed <= 0 or remaining_bytes <= 0:
            return None
        return remaining_bytes / speed

    def format_speed(self, speed: float | None = None) -> str:
        """Human-readable speed string."""
        bps = speed if speed is not None else self.current_speed
        if bps <= 0:
            return "0 B/s"
        units = ["B/s", "KiB/s", "MiB/s", "GiB/s"]
        val = bps
        for unit in units:
            if val < 1024:
                return f"{val:.1f} {unit}"
            val /= 1024
        return f"{val:.1f} TiB/s"
