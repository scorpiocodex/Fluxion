"""Fluxion core download engine — orchestrates protocols, performance, and security."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import AsyncIterator, Callable
from urllib.parse import urlparse

import httpx

from fluxion.exceptions import NetworkError, SecurityError
from fluxion.models import (
    BenchResult,
    FetchRequest,
    FetchResult,
    FluxMode,
    ProbeResult,
    Protocol,
    TransferPhase,
    TransferStats,
)
from fluxion.performance.bandwidth import BandwidthEstimator
from fluxion.performance.chunker import AdaptiveChunker, ChunkPlan
from fluxion.performance.optimizer import ConnectionOptimizer
from fluxion.performance.retry import RetryClassifier, RetryVerdict
from fluxion.performance.scheduler import ChunkResult, ParallelScheduler
from fluxion.security.integrity import IntegrityVerifier
from fluxion.security.proxy import ProxyDetector
from fluxion.security.tls import TLSInspector
from fluxion.stealth.context import StealthContext
from fluxion.stealth.cookies import CookieJar
from fluxion.stealth.profiles import get_profile

ProgressCallback = Callable[[TransferStats], None]


class FluxionEngine:
    """The main download/upload engine.

    Coordinates HTTP client, parallel scheduling, adaptive chunking,
    retry classification, and integrity verification.
    """

    def __init__(
        self,
        max_connections: int = 8,
        timeout: float = 30.0,
        verify_tls: bool = True,
        proxy: str | None = None,
        user_agent: str = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        enable_http2: bool = True,
    ) -> None:
        self._max_connections = max_connections
        self._timeout = timeout
        self._verify_tls = verify_tls
        self._proxy = proxy
        self._user_agent = user_agent
        self._enable_http2 = enable_http2

        self._retry = RetryClassifier()
        self._bandwidth = BandwidthEstimator()
        self._tls_inspector = TLSInspector(verify=verify_tls)

        proxy_config = ProxyDetector.detect()
        self._proxies = ProxyDetector.as_httpx_dict(proxy_config)
        if proxy:
            self._proxies = {"http://": proxy, "https://": proxy}

    def _build_client(
        self, extra_headers: dict[str, str] | None = None
    ) -> httpx.AsyncClient:
        headers = {"User-Agent": self._user_agent}
        if extra_headers:
            headers.update(extra_headers)
        return httpx.AsyncClient(
            http2=self._enable_http2,
            verify=self._verify_tls,
            proxy=self._proxies,  # type: ignore[arg-type]
            timeout=httpx.Timeout(self._timeout),
            headers=headers,
            follow_redirects=True,
            limits=httpx.Limits(
                max_connections=self._max_connections * 2,
                max_keepalive_connections=self._max_connections,
            ),
        )

    # ------------------------------------------------------------------
    # Stealth header resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_stealth_headers(request: FetchRequest) -> dict[str, str]:
        """Build merged stealth headers from request fields."""
        profile = None
        if request.browser_profile:
            profile = get_profile(request.browser_profile)

        cookie_jar = CookieJar()
        for name, value in request.cookies.items():
            cookie_jar.add_raw(f"{name}={value}")

        ctx = StealthContext(
            profile=profile,
            cookie_jar=cookie_jar,
            custom_headers=dict(request.headers),
            referer=request.referer,
        )
        return ctx.build_headers()

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------

    async def probe(
        self, url: str, extra_headers: dict[str, str] | None = None,
    ) -> ProbeResult:
        """Perform a network probe (HEAD request + TLS inspection)."""
        result = ProbeResult(url=url)

        # TLS inspection (synchronous, uses raw socket)
        parsed = urlparse(url)
        if parsed.scheme == "https":
            try:
                cert_info = self._tls_inspector.inspect(url)
                result.tls_version = cert_info.tls_version
                result.tls_cipher = cert_info.cipher
                result.certificate_issuer = cert_info.issuer.get("organizationName", "")
                result.certificate_expiry = cert_info.not_after
            except SecurityError:
                pass

        async with self._build_client(extra_headers=extra_headers) as client:
            max_probe_retries = 3
            for attempt in range(max_probe_retries + 1):
                t0 = time.monotonic()
                try:
                    resp = await client.head(url)
                    latency = (time.monotonic() - t0) * 1000
                    # Some servers block HEAD requests — fall back to GET
                    if resp.status_code in (403, 405, 501):
                        t0 = time.monotonic()
                        resp = await client.get(url, headers={"Range": "bytes=0-0"})
                        latency = (time.monotonic() - t0) * 1000
                except httpx.HTTPError as exc:
                    raise NetworkError(
                        f"Probe failed: {exc}",
                        suggestion="Check the URL and network connectivity.",
                    ) from exc

                # Retry on transient server errors (429, 503, 502, 500)
                if resp.status_code in (429, 500, 502, 503) and attempt < max_probe_retries:
                    retry_after = resp.headers.get("retry-after")
                    delay = float(retry_after) if retry_after and retry_after.isdigit() else (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue

                if resp.status_code >= 400:
                    raise NetworkError(
                        f"HTTP {resp.status_code}: {resp.reason_phrase or 'Error'}",
                        status_code=resp.status_code,
                        suggestion="Check the URL and ensure the resource is accessible.",
                    )
                break  # Success — exit retry loop

            result.latency_ms = round(latency, 2)
            result.http_version = resp.http_version or ""
            result.server = resp.headers.get("server", "")
            result.supports_range = resp.headers.get("accept-ranges", "").lower() == "bytes"
            cl = resp.headers.get("content-length")
            # Range response returns partial size; use content-range for full size
            if resp.status_code == 206:
                cr = resp.headers.get("content-range", "")
                if "/" in cr:
                    total = cr.rsplit("/", 1)[-1]
                    result.content_length = int(total) if total.isdigit() else None
                    result.supports_range = True
                else:
                    result.content_length = int(cl) if cl else None
            else:
                result.content_length = int(cl) if cl else None
            result.content_type = resp.headers.get("content-type", "")
            result.headers = dict(resp.headers)

            # Resolve IP via parsed url
            import socket

            try:
                result.resolved_ip = socket.gethostbyname(parsed.hostname or "")
            except OSError:
                pass

        return result

    # ------------------------------------------------------------------
    # Bench
    # ------------------------------------------------------------------

    async def bench(self, url: str, iterations: int = 10) -> BenchResult:
        """Benchmark latency and throughput to *url*."""
        latencies: list[float] = []
        failures = 0

        async with self._build_client() as client:
            for _ in range(iterations):
                t0 = time.monotonic()
                try:
                    resp = await client.head(url)
                    elapsed_ms = (time.monotonic() - t0) * 1000
                    if resp.is_success:
                        latencies.append(elapsed_ms)
                    else:
                        failures += 1
                except httpx.HTTPError:
                    failures += 1

        if not latencies:
            return BenchResult(
                url=url,
                requests_completed=0,
                requests_failed=failures,
            )

        latencies.sort()
        n = len(latencies)
        avg = sum(latencies) / n
        jitter = max(latencies) - min(latencies) if n > 1 else 0.0

        def percentile(p: float) -> float:
            k = (n - 1) * p
            f = int(k)
            c = f + 1 if f + 1 < n else f
            return latencies[f] + (k - f) * (latencies[c] - latencies[f])

        # Stability: 1.0 = perfect, lower = worse.  Based on coefficient of variation.
        mean = avg
        variance = sum((x - mean) ** 2 for x in latencies) / n
        stddev = variance**0.5
        cv = stddev / mean if mean > 0 else 0
        stability = max(0.0, min(1.0, 1.0 - cv))

        # Throughput measurement: GET first 1MB to measure actual speed
        throughput_mbps = 0.0
        try:
            range_header = {"Range": "bytes=0-1048575"}
            t0 = time.monotonic()
            async with self._build_client() as client:
                resp = await client.get(url, headers=range_header)
                elapsed_sec = time.monotonic() - t0
                data_bytes = len(resp.content)
                if elapsed_sec > 0 and data_bytes > 0:
                    throughput_mbps = round((data_bytes * 8) / (elapsed_sec * 1_000_000), 3)
        except (httpx.HTTPError, OSError):
            pass

        return BenchResult(
            url=url,
            latency_min_ms=round(latencies[0], 2),
            latency_max_ms=round(latencies[-1], 2),
            latency_avg_ms=round(avg, 2),
            latency_p50_ms=round(percentile(0.50), 2),
            latency_p95_ms=round(percentile(0.95), 2),
            latency_p99_ms=round(percentile(0.99), 2),
            jitter_ms=round(jitter, 2),
            throughput_mbps=throughput_mbps,
            stability_score=round(stability, 3),
            requests_completed=n,
            requests_failed=failures,
        )

    # ------------------------------------------------------------------
    # Fetch (parallel download)
    # ------------------------------------------------------------------

    async def fetch(
        self,
        request: FetchRequest,
        on_progress: ProgressCallback | None = None,
    ) -> FetchResult:
        """Download a resource with parallel range requests and adaptive chunking."""
        parsed = urlparse(request.url)
        scheme = parsed.scheme.lower()

        # Protocol dispatch for non-HTTP schemes
        if scheme in ("ftp", "sftp", "scp"):
            return await self._fetch_non_http(request, scheme)

        stats = TransferStats(phase=TransferPhase.RESOLVING)
        self._notify(on_progress, stats)

        # Resolve stealth headers once
        stealth_headers = self._resolve_stealth_headers(request)

        # Phase: probe
        probe = await self.probe(request.url, extra_headers=stealth_headers)
        stats.phase = TransferPhase.CONNECTING
        self._notify(on_progress, stats)

        output_path = request.output or Path(self._filename_from_url(request.url))
        protocol = self._detect_protocol(probe)

        stats.phase = TransferPhase.TLS
        self._notify(on_progress, stats)

        stats.phase = TransferPhase.PROTOCOL_LOCK
        self._notify(on_progress, stats)

        total_size = probe.content_length
        supports_range = probe.supports_range and total_size is not None

        # If resume is requested but server doesn't support ranges,
        # silently fall back to a fresh download instead of erroring.
        if request.resume and not supports_range and output_path.exists():
            request = request.model_copy(update={"resume": False})

        # Determine resume offset
        resume_offset = 0
        if request.resume and output_path.exists() and supports_range:
            resume_offset = output_path.stat().st_size
            if total_size and resume_offset >= total_size:
                # Already complete
                stats.phase = TransferPhase.COMPLETE
                self._notify(on_progress, stats)
                return FetchResult(
                    url=request.url,
                    output_path=output_path,
                    bytes_downloaded=resume_offset,
                    elapsed_seconds=0,
                    speed_bytes_per_sec=0,
                    protocol_used=protocol,
                    resumed=True,
                )

        start_time = time.monotonic()
        stats.phase = TransferPhase.STREAM
        stats.bytes_total = total_size

        if supports_range and total_size and total_size > request.chunk_size * 2:
            # Parallel download
            stats.flux_mode = FluxMode.PARALLEL
            result = await self._parallel_download(
                request, output_path, total_size, resume_offset,
                protocol, stats, on_progress, stealth_headers,
            )
        else:
            # Single-stream download
            stats.flux_mode = FluxMode.SINGLE
            result = await self._stream_download(
                request, output_path, protocol, stats, on_progress, stealth_headers,
            )

        elapsed = time.monotonic() - start_time

        # Phase: verify
        stats.phase = TransferPhase.VERIFY
        self._notify(on_progress, stats)
        sha256 = IntegrityVerifier.compute_sha256(output_path)

        stats.phase = TransferPhase.COMPLETE
        self._notify(on_progress, stats)

        return FetchResult(
            url=request.url,
            output_path=output_path,
            bytes_downloaded=result,
            elapsed_seconds=round(elapsed, 3),
            speed_bytes_per_sec=round(result / max(elapsed, 0.001), 2),
            protocol_used=protocol,
            sha256=sha256,
            resumed=resume_offset > 0,
        )

    async def _fetch_non_http(
        self, request: FetchRequest, scheme: str
    ) -> FetchResult:
        """Dispatch to FTP/SFTP/SCP protocol handlers."""
        output_path = request.output or Path(self._filename_from_url(request.url))
        start_time = time.monotonic()

        if scheme == "ftp":
            from fluxion.protocols.ftp import FTPHandler

            handler = FTPHandler(timeout=request.timeout)
            downloaded = await handler.download(request.url, output_path)
            protocol = Protocol.FTP
        elif scheme == "sftp":
            from fluxion.protocols.sftp import SFTPHandler

            handler = SFTPHandler(timeout=request.timeout)  # type: ignore[assignment]
            downloaded = await handler.download_sftp(request.url, output_path)
            protocol = Protocol.SFTP
        else:  # scp
            from fluxion.protocols.sftp import SFTPHandler

            handler = SFTPHandler(timeout=request.timeout)  # type: ignore[assignment]
            downloaded = await handler.download_scp(request.url, output_path)
            protocol = Protocol.SCP

        elapsed = time.monotonic() - start_time
        sha256 = IntegrityVerifier.compute_sha256(output_path)

        return FetchResult(
            url=request.url,
            output_path=output_path,
            bytes_downloaded=downloaded,
            elapsed_seconds=round(elapsed, 3),
            speed_bytes_per_sec=round(downloaded / max(elapsed, 0.001), 2),
            protocol_used=protocol,
            sha256=sha256,
        )

    async def _parallel_download(
        self,
        request: FetchRequest,
        output_path: Path,
        total_size: int,
        offset: int,
        protocol: Protocol,
        stats: TransferStats,
        on_progress: ProgressCallback | None,
        stealth_headers: dict[str, str] | None = None,
    ) -> int:
        """Execute a parallel chunked download."""
        chunker = AdaptiveChunker(initial_chunk_size=request.chunk_size)
        optimizer = ConnectionOptimizer(
            initial=min(request.max_connections, 4),
            maximum=request.max_connections,
        )
        bandwidth = self._bandwidth
        retry = self._retry

        scheduler = ParallelScheduler(
            total_size=total_size,
            chunker=chunker,
            optimizer=optimizer,
            bandwidth=bandwidth,
            offset=offset,
        )

        async with self._build_client(extra_headers=stealth_headers) as client:

            async def download_chunk(plan: ChunkPlan) -> ChunkResult:
                headers = {"Range": f"bytes={plan.start}-{plan.end}"}
                for attempt in range(request.max_retries + 1):
                    t0 = time.monotonic()
                    try:
                        resp = await client.get(request.url, headers=headers)
                        elapsed = time.monotonic() - t0

                        # Check for retryable HTTP status
                        if resp.status_code >= 400:
                            decision = retry.classify_status(resp.status_code, attempt)
                            if retry.should_retry(decision, attempt):
                                await asyncio.sleep(decision.delay_sec)
                                continue
                            # Fatal status — return failure
                            return ChunkResult(
                                index=plan.index,
                                start=plan.start,
                                end=plan.end,
                                data=b"",
                                elapsed_sec=elapsed,
                                success=False,
                                error=f"HTTP {resp.status_code}",
                            )

                        return ChunkResult(
                            index=plan.index,
                            start=plan.start,
                            end=plan.end,
                            data=resp.content,
                            elapsed_sec=elapsed,
                        )
                    except httpx.HTTPError as exc:
                        elapsed = time.monotonic() - t0
                        decision = retry.classify_exception(exc, attempt)
                        if retry.should_retry(decision, attempt):
                            await asyncio.sleep(decision.delay_sec)
                            continue
                        return ChunkResult(
                            index=plan.index,
                            start=plan.start,
                            end=plan.end,
                            data=b"",
                            elapsed_sec=elapsed,
                            success=False,
                            error=str(exc),
                        )

                # Exhausted retries
                return ChunkResult(
                    index=plan.index,
                    start=plan.start,
                    end=plan.end,
                    data=b"",
                    elapsed_sec=0,
                    success=False,
                    error="Max retries exhausted",
                )

            def progress_cb(completed: int, total: int) -> None:
                stats.bytes_downloaded = completed + offset
                stats.speed_bytes_per_sec = bandwidth.current_speed
                stats.active_connections = optimizer.concurrency
                remaining = total - completed
                stats.eta_seconds = bandwidth.eta_seconds(remaining)
                self._notify(on_progress, stats)

            results = await scheduler.execute(download_chunk, on_progress=progress_cb)

        # Assemble file
        file_mode = "r+b" if offset > 0 and output_path.exists() else "wb"
        with output_path.open(file_mode) as f:
            for chunk_result in results:
                if chunk_result.success:
                    f.seek(chunk_result.start)
                    f.write(chunk_result.data)

        return sum(len(r.data) for r in results if r.success) + offset

    async def _stream_download(
        self,
        request: FetchRequest,
        output_path: Path,
        protocol: Protocol,
        stats: TransferStats,
        on_progress: ProgressCallback | None,
        stealth_headers: dict[str, str] | None = None,
    ) -> int:
        """Single-stream download with progress and retry."""
        retry = self._retry

        for attempt in range(request.max_retries + 1):
            downloaded = 0
            try:
                async with self._build_client(extra_headers=stealth_headers) as client:
                    async with client.stream("GET", request.url) as resp:
                        if resp.status_code >= 400:
                            decision = retry.classify_status(resp.status_code, attempt)
                            if retry.should_retry(decision, attempt):
                                await asyncio.sleep(decision.delay_sec)
                                continue
                            raise NetworkError(
                                f"HTTP {resp.status_code}: {resp.reason_phrase or 'Error'}",
                                status_code=resp.status_code,
                                suggestion="Check the URL and ensure the resource exists.",
                            )
                        total = resp.headers.get("content-length")
                        if total:
                            stats.bytes_total = int(total)

                        last_time = time.monotonic()
                        with output_path.open("wb") as f:
                            async for chunk in resp.aiter_bytes(chunk_size=65536):
                                f.write(chunk)
                                downloaded += len(chunk)
                                now = time.monotonic()
                                elapsed = now - last_time
                                last_time = now
                                self._bandwidth.record(len(chunk), max(elapsed, 0.001))
                                stats.bytes_downloaded = downloaded
                                stats.speed_bytes_per_sec = self._bandwidth.current_speed
                                if stats.bytes_total:
                                    remaining = stats.bytes_total - downloaded
                                    stats.eta_seconds = self._bandwidth.eta_seconds(remaining)
                                self._notify(on_progress, stats)

                return downloaded

            except NetworkError:
                raise
            except httpx.HTTPError as exc:
                decision = retry.classify_exception(exc, attempt)
                if retry.should_retry(decision, attempt):
                    await asyncio.sleep(decision.delay_sec)
                    continue
                raise NetworkError(
                    f"Stream download failed: {exc}",
                    suggestion="Check the URL and network connectivity.",
                ) from exc

        raise NetworkError(
            "Stream download failed after max retries.",
            suggestion="Try again later or increase --timeout.",
        )

    # ------------------------------------------------------------------
    # Stream (async iterator)
    # ------------------------------------------------------------------

    async def stream(self, url: str, headers: dict[str, str] | None = None) -> AsyncIterator[bytes]:
        """Yield chunks from a streaming response."""
        try:
            async with self._build_client(extra_headers=headers) as client:
                async with client.stream("GET", url) as resp:
                    if resp.status_code >= 400:
                        raise NetworkError(
                            f"HTTP {resp.status_code}: {resp.reason_phrase or 'Error'}",
                            status_code=resp.status_code,
                            suggestion="Check the URL.",
                        )
                    async for chunk in resp.aiter_bytes(chunk_size=65536):
                        yield chunk
        except httpx.HTTPError as exc:
            raise NetworkError(
                f"Stream failed: {exc}",
                suggestion="Check the URL and network connectivity.",
            ) from exc

    # ------------------------------------------------------------------
    # Mirror
    # ------------------------------------------------------------------

    async def mirror(
        self,
        urls: list[str],
        output: Path | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> FetchResult:
        """Try multiple mirror URLs, using the fastest available."""
        # Probe all mirrors in parallel
        async def _probe_mirror(mirror_url: str) -> tuple[str, float] | None:
            try:
                result = await self.probe(mirror_url)
                return (mirror_url, result.latency_ms)
            except NetworkError:
                return None

        tasks = [_probe_mirror(u) for u in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        probes: list[tuple[str, float]] = [
            r for r in results if isinstance(r, tuple)
        ]

        if not probes:
            raise NetworkError(
                "All mirrors failed probing.",
                suggestion="Check URLs and connectivity.",
            )

        probes.sort(key=lambda x: x[1])
        best_url = probes[0][0]

        req = FetchRequest(url=best_url, output=output)
        return await self.fetch(req, on_progress=on_progress)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _detect_protocol(self, probe: ProbeResult) -> Protocol:
        ver = probe.http_version.lower()
        if "h3" in ver or "3" in ver:
            return Protocol.HTTP3
        if "h2" in ver or "2" in ver:
            return Protocol.HTTP2
        return Protocol.HTTP1

    @staticmethod
    def _filename_from_url(url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        if path:
            name = path.split("/")[-1]
            if name:
                return name
        return "download"

    @staticmethod
    def _notify(callback: ProgressCallback | None, stats: TransferStats) -> None:
        if callback:
            callback(stats)
