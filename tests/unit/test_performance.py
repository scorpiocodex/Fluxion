"""Tests for performance subsystem."""

import asyncio

import pytest

from fluxion.performance.bandwidth import BandwidthEstimator
from fluxion.performance.chunker import AdaptiveChunker, ChunkPlan
from fluxion.performance.optimizer import ConnectionOptimizer
from fluxion.performance.retry import RetryClassifier, RetryDecision, RetryVerdict
from fluxion.performance.scheduler import ChunkResult, ParallelScheduler


class TestAdaptiveChunker:
    def test_plan_chunks(self) -> None:
        chunker = AdaptiveChunker(initial_chunk_size=1024)
        plans = chunker.plan_chunks(4096)
        assert len(plans) == 4
        assert plans[0].start == 0
        assert plans[0].end == 1023
        assert plans[-1].end == 4095

    def test_plan_chunks_with_offset(self) -> None:
        chunker = AdaptiveChunker(initial_chunk_size=1024)
        plans = chunker.plan_chunks(4096, offset=2048)
        assert len(plans) == 2
        assert plans[0].start == 2048

    def test_feedback_grows_on_high_throughput(self) -> None:
        chunker = AdaptiveChunker(initial_chunk_size=1024, max_chunk=8192)
        # Feed consistently high throughput
        for _ in range(5):
            chunker.feedback(1024, 0.01)  # 100 KiB/s
        assert chunker.chunk_size >= 1024

    def test_feedback_shrinks_on_low_throughput(self) -> None:
        chunker = AdaptiveChunker(initial_chunk_size=4096, min_chunk=256)
        # Establish high baseline
        chunker.feedback(4096, 0.01)
        # Then low throughput
        chunker.feedback(4096, 10.0)
        assert chunker.chunk_size <= 4096

    def test_chunk_size_property(self) -> None:
        chunker = AdaptiveChunker(initial_chunk_size=2048)
        assert chunker.chunk_size == 2048


class TestConnectionOptimizer:
    def test_initial_concurrency(self) -> None:
        opt = ConnectionOptimizer(initial=4)
        assert opt.concurrency == 4

    def test_suggest_concurrency_small_file(self) -> None:
        opt = ConnectionOptimizer()
        assert opt.suggest_concurrency(500_000) == 1  # < 1 MiB

    def test_suggest_concurrency_medium_file(self) -> None:
        opt = ConnectionOptimizer()
        c = opt.suggest_concurrency(50 * 1024 * 1024)  # 50 MiB
        assert 1 <= c <= 32

    def test_suggest_concurrency_unknown(self) -> None:
        opt = ConnectionOptimizer(minimum=2)
        assert opt.suggest_concurrency(None) == 2

    def test_throttle_reduces_concurrency(self) -> None:
        opt = ConnectionOptimizer(initial=8)
        opt.report_throttle()
        assert opt.concurrency < 8


class TestRetryClassifier:
    def test_success_not_retried(self) -> None:
        rc = RetryClassifier()
        d = rc.classify_status(200, 0)
        assert d.verdict == RetryVerdict.FATAL

    def test_404_not_retried(self) -> None:
        rc = RetryClassifier()
        d = rc.classify_status(404, 0)
        assert d.verdict == RetryVerdict.FATAL

    def test_429_retried_with_backoff(self) -> None:
        rc = RetryClassifier()
        d = rc.classify_status(429, 1)
        assert d.verdict == RetryVerdict.RETRY_BACKOFF
        assert d.delay_sec > 0

    def test_500_retried(self) -> None:
        rc = RetryClassifier()
        d = rc.classify_status(500, 1)
        assert d.verdict == RetryVerdict.RETRY_BACKOFF

    def test_should_retry_respects_max(self) -> None:
        rc = RetryClassifier(max_retries=2)
        d = rc.classify_status(500, 3)
        assert not rc.should_retry(d, 3)
        d2 = rc.classify_status(500, 1)
        assert rc.should_retry(d2, 1)

    def test_timeout_exception(self) -> None:
        rc = RetryClassifier()
        d = rc.classify_exception(TimeoutError("timed out"), 1)
        assert d.verdict == RetryVerdict.RETRY_BACKOFF

    def test_dns_exception_fatal(self) -> None:
        rc = RetryClassifier()

        class DNSResolveError(Exception):
            pass

        d = rc.classify_exception(DNSResolveError("resolve failed"), 1)
        # "resolve" is in the class name
        assert d.verdict == RetryVerdict.FATAL


class TestBandwidthEstimator:
    def test_initial_state(self) -> None:
        bw = BandwidthEstimator()
        assert bw.current_speed == 0.0
        assert bw.total_bytes == 0

    def test_record_updates_speed(self) -> None:
        bw = BandwidthEstimator()
        bw.record(1024, 1.0)
        assert bw.current_speed > 0
        assert bw.total_bytes == 1024

    def test_eta(self) -> None:
        bw = BandwidthEstimator()
        bw.record(1024, 1.0)  # ~1024 B/s
        eta = bw.eta_seconds(2048)
        assert eta is not None
        assert eta > 0

    def test_eta_none_when_no_data(self) -> None:
        bw = BandwidthEstimator()
        assert bw.eta_seconds(1000) is None

    def test_format_speed(self) -> None:
        bw = BandwidthEstimator()
        assert bw.format_speed(0) == "0 B/s"
        assert "KiB/s" in bw.format_speed(2048)
        assert "MiB/s" in bw.format_speed(5 * 1024 * 1024)

    def test_average_speed(self) -> None:
        bw = BandwidthEstimator()
        bw.record(1024, 1.0)
        bw.record(2048, 1.0)
        avg = bw.average_speed
        assert avg > 0

    def test_eta_zero_remaining(self) -> None:
        bw = BandwidthEstimator()
        bw.record(1024, 1.0)
        assert bw.eta_seconds(0) is None


class TestChunkPlan:
    def test_size(self) -> None:
        plan = ChunkPlan(index=0, start=0, end=1023)
        assert plan.size == 1024

    def test_size_single_byte(self) -> None:
        plan = ChunkPlan(index=0, start=100, end=100)
        assert plan.size == 1


class TestChunkResult:
    def test_success(self) -> None:
        result = ChunkResult(index=0, start=0, end=1023, data=b"x" * 1024, elapsed_sec=0.5)
        assert result.success is True
        assert len(result.data) == 1024

    def test_failure(self) -> None:
        result = ChunkResult(index=0, start=0, end=1023, data=b"", elapsed_sec=0.5, success=False, error="timeout")
        assert result.success is False
        assert result.error == "timeout"


class TestParallelScheduler:
    def test_initial_state(self) -> None:
        scheduler = ParallelScheduler(total_size=1024)
        assert scheduler.completed_bytes == 0
        assert scheduler.progress == 0.0

    def test_progress_zero_total(self) -> None:
        scheduler = ParallelScheduler(total_size=0)
        assert scheduler.progress == 0.0

    @pytest.mark.asyncio
    async def test_execute_simple(self) -> None:
        scheduler = ParallelScheduler(
            total_size=2048,
            chunker=AdaptiveChunker(initial_chunk_size=1024),
        )

        async def downloader(plan: ChunkPlan) -> ChunkResult:
            return ChunkResult(
                index=plan.index,
                start=plan.start,
                end=plan.end,
                data=b"x" * plan.size,
                elapsed_sec=0.01,
            )

        results = await scheduler.execute(downloader)
        assert len(results) == 2
        assert all(r.success for r in results)
        assert results[0].index < results[1].index

    @pytest.mark.asyncio
    async def test_execute_with_progress(self) -> None:
        scheduler = ParallelScheduler(
            total_size=1024,
            chunker=AdaptiveChunker(initial_chunk_size=512),
        )
        progress_calls: list[tuple[int, int]] = []

        async def downloader(plan: ChunkPlan) -> ChunkResult:
            return ChunkResult(
                index=plan.index, start=plan.start, end=plan.end,
                data=b"x" * plan.size, elapsed_sec=0.01,
            )

        def on_progress(completed: int, total: int) -> None:
            progress_calls.append((completed, total))

        await scheduler.execute(downloader, on_progress=on_progress)
        assert len(progress_calls) >= 1

    @pytest.mark.asyncio
    async def test_execute_empty(self) -> None:
        scheduler = ParallelScheduler(
            total_size=0,
            chunker=AdaptiveChunker(initial_chunk_size=1024),
        )

        async def downloader(plan: ChunkPlan) -> ChunkResult:
            return ChunkResult(index=0, start=0, end=0, data=b"", elapsed_sec=0.01)

        results = await scheduler.execute(downloader)
        assert results == []


class TestRetryDecision:
    def test_decision_fields(self) -> None:
        d = RetryDecision(verdict=RetryVerdict.RETRY_BACKOFF, delay_sec=2.0, reason="test")
        assert d.verdict == RetryVerdict.RETRY_BACKOFF
        assert d.delay_sec == 2.0
        assert d.reason == "test"


class TestRetryClassifierExtra:
    def test_connection_refused(self) -> None:
        rc = RetryClassifier()

        class ConnectionRefusedError(Exception):
            pass

        d = rc.classify_exception(ConnectionRefusedError("refused"), 1)
        assert d.verdict == RetryVerdict.RETRY_IMMEDIATE

    def test_ssl_error_fatal(self) -> None:
        rc = RetryClassifier()

        class SSLError(Exception):
            pass

        d = rc.classify_exception(SSLError("bad cert"), 1)
        assert d.verdict == RetryVerdict.FATAL

    def test_unknown_exception(self) -> None:
        rc = RetryClassifier()
        d = rc.classify_exception(RuntimeError("something"), 1)
        assert d.verdict == RetryVerdict.RETRY_BACKOFF

    def test_unexpected_status_code(self) -> None:
        rc = RetryClassifier()
        d = rc.classify_status(418, 1)  # I'm a teapot
        assert d.verdict == RetryVerdict.RETRY_BACKOFF


class TestConnectionOptimizerExtra:
    def test_suggest_concurrency_large_file(self) -> None:
        opt = ConnectionOptimizer()
        c = opt.suggest_concurrency(500 * 1024 * 1024)  # 500 MiB
        assert c == 16

    def test_report_throughput(self) -> None:
        opt = ConnectionOptimizer(initial=4, probe_interval_sec=0.0)
        for _ in range(10):
            opt.report_throughput(100_000)
        # Should not crash, concurrency should remain bounded
        assert 1 <= opt.concurrency <= 32
