"""Parallel download scheduler — orchestrates concurrent chunk downloads."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Callable, Awaitable

from fluxion.performance.chunker import AdaptiveChunker, ChunkPlan
from fluxion.performance.optimizer import ConnectionOptimizer
from fluxion.performance.bandwidth import BandwidthEstimator


@dataclass
class ChunkResult:
    """Result of downloading a single chunk."""

    index: int
    start: int
    end: int
    data: bytes
    elapsed_sec: float
    success: bool = True
    error: str = ""


# Type alias for the async function that downloads a single chunk
ChunkDownloader = Callable[[ChunkPlan], Awaitable[ChunkResult]]


class ParallelScheduler:
    """Schedule and execute parallel chunk downloads with adaptive control.

    Coordinates the AdaptiveChunker, ConnectionOptimizer, and BandwidthEstimator
    to maximise throughput while respecting server limits.
    """

    def __init__(
        self,
        total_size: int,
        chunker: AdaptiveChunker | None = None,
        optimizer: ConnectionOptimizer | None = None,
        bandwidth: BandwidthEstimator | None = None,
        offset: int = 0,
    ) -> None:
        self._total_size = total_size
        self._offset = offset
        self._chunker = chunker or AdaptiveChunker()
        self._optimizer = optimizer or ConnectionOptimizer()
        self._bandwidth = bandwidth or BandwidthEstimator()
        self._completed_bytes = 0
        self._start_time = 0.0
        self._results: dict[int, ChunkResult] = {}

    @property
    def completed_bytes(self) -> int:
        return self._completed_bytes

    @property
    def progress(self) -> float:
        if self._total_size <= 0:
            return 0.0
        return self._completed_bytes / self._total_size

    async def execute(
        self,
        downloader: ChunkDownloader,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> list[ChunkResult]:
        """Execute the parallel download, calling *downloader* for each chunk.

        Returns completed ChunkResults sorted by index.
        """
        self._start_time = time.monotonic()
        chunks = self._chunker.plan_chunks(self._total_size, self._offset)

        if not chunks:
            return []

        concurrency = self._optimizer.suggest_concurrency(self._total_size)
        semaphore = asyncio.Semaphore(concurrency)
        results: list[ChunkResult] = []
        lock = asyncio.Lock()

        async def _run_chunk(plan: ChunkPlan) -> None:
            async with semaphore:
                t0 = time.monotonic()
                result = await downloader(plan)
                elapsed = time.monotonic() - t0

                if result.success:
                    self._chunker.feedback(result.end - result.start + 1, elapsed)
                    self._bandwidth.record(len(result.data), elapsed)
                    throughput = self._bandwidth.current_speed
                    self._optimizer.report_throughput(throughput)

                    async with lock:
                        self._completed_bytes += len(result.data)
                        results.append(result)
                        if on_progress:
                            on_progress(self._completed_bytes, self._total_size)
                else:
                    async with lock:
                        results.append(result)

        tasks = [asyncio.create_task(_run_chunk(chunk)) for chunk in chunks]
        await asyncio.gather(*tasks, return_exceptions=True)

        results.sort(key=lambda r: r.index)
        return results
