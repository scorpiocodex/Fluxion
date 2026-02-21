"""Adaptive chunk size management for parallel downloads."""

from __future__ import annotations

from dataclasses import dataclass

# Default bounds
MIN_CHUNK = 256 * 1024         # 256 KiB
MAX_CHUNK = 16 * 1024 * 1024   # 16 MiB
INITIAL_CHUNK = 1024 * 1024    # 1 MiB


@dataclass
class ChunkPlan:
    """A range request plan for one chunk."""

    index: int
    start: int
    end: int  # inclusive

    @property
    def size(self) -> int:
        return self.end - self.start + 1


class AdaptiveChunker:
    """Dynamically resizes download chunks based on throughput feedback.

    Algorithm:
    - If throughput increases: grow chunk size (up to MAX_CHUNK).
    - If throughput drops: shrink chunk size (down to MIN_CHUNK).
    - Maintains an exponential moving average of throughput.
    """

    def __init__(
        self,
        initial_chunk_size: int = INITIAL_CHUNK,
        min_chunk: int = MIN_CHUNK,
        max_chunk: int = MAX_CHUNK,
        ema_alpha: float = 0.3,
    ) -> None:
        self._chunk_size = initial_chunk_size
        self._min = min_chunk
        self._max = max_chunk
        self._alpha = ema_alpha
        self._ema_throughput: float | None = None
        self._samples: list[float] = []

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    def plan_chunks(self, total_size: int, offset: int = 0) -> list[ChunkPlan]:
        """Generate a list of chunk plans covering *total_size* bytes from *offset*."""
        chunks: list[ChunkPlan] = []
        pos = offset
        idx = 0
        while pos < total_size:
            end = min(pos + self._chunk_size - 1, total_size - 1)
            chunks.append(ChunkPlan(index=idx, start=pos, end=end))
            pos = end + 1
            idx += 1
        return chunks

    def feedback(self, bytes_transferred: int, elapsed_sec: float) -> None:
        """Feed throughput data to adapt chunk sizing."""
        if elapsed_sec <= 0:
            return
        throughput = bytes_transferred / elapsed_sec
        self._samples.append(throughput)

        if self._ema_throughput is None:
            self._ema_throughput = throughput
        else:
            self._ema_throughput = (
                self._alpha * throughput + (1 - self._alpha) * self._ema_throughput
            )

        # Adapt: if current throughput is above average, increase; else shrink
        if throughput >= self._ema_throughput:
            self._chunk_size = min(self._chunk_size * 2, self._max)
        else:
            self._chunk_size = max(self._chunk_size // 2, self._min)

    @property
    def avg_throughput(self) -> float:
        return self._ema_throughput or 0.0
