"""Tests for core engine — uses mocked network layer."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from fluxion.core.engine import FluxionEngine
from fluxion.exceptions import NetworkError
from fluxion.models import FetchRequest, ProbeResult, Protocol
from fluxion.security.integrity import IntegrityVerifier


class TestEngineProbe:
    @pytest.mark.asyncio
    async def test_probe_success(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.http_version = "HTTP/2"
        mock_response.headers = {
            "server": "nginx",
            "accept-ranges": "bytes",
            "content-length": "1024",
            "content-type": "application/octet-stream",
        }
        mock_response.is_success = True

        engine = FluxionEngine(verify_tls=False)

        with patch.object(engine, "_build_client") as mock_client_builder:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client_builder.return_value = mock_client

            with patch("fluxion.core.engine.TLSInspector"):
                result = await engine.probe("http://example.com/file")

            assert result.http_version == "HTTP/2"
            assert result.server == "nginx"
            assert result.supports_range is True
            assert result.content_length == 1024

    @pytest.mark.asyncio
    async def test_probe_failure(self) -> None:
        engine = FluxionEngine(verify_tls=False)

        with patch.object(engine, "_build_client") as mock_client_builder:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.head = AsyncMock(side_effect=httpx.ConnectError("refused"))
            mock_client_builder.return_value = mock_client

            with pytest.raises(NetworkError, match="Probe failed"):
                await engine.probe("http://example.com/nope")

    @pytest.mark.asyncio
    async def test_probe_no_range_support(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.http_version = "HTTP/1.1"
        mock_response.headers = {
            "server": "apache",
            "content-type": "text/html",
        }

        engine = FluxionEngine(verify_tls=False)

        with patch.object(engine, "_build_client") as mock_client_builder:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client_builder.return_value = mock_client

            result = await engine.probe("http://example.com/page")

        assert result.supports_range is False
        assert result.content_length is None


class TestEngineBench:
    @pytest.mark.asyncio
    async def test_bench_success(self) -> None:
        mock_response = MagicMock()
        mock_response.is_success = True

        engine = FluxionEngine(verify_tls=False)

        with patch.object(engine, "_build_client") as mock_client_builder:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client_builder.return_value = mock_client

            result = await engine.bench("http://example.com", iterations=3)

        assert result.requests_completed == 3
        assert result.requests_failed == 0
        assert result.latency_avg_ms >= 0

    @pytest.mark.asyncio
    async def test_bench_all_failures(self) -> None:
        engine = FluxionEngine(verify_tls=False)

        with patch.object(engine, "_build_client") as mock_client_builder:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.head = AsyncMock(side_effect=httpx.ConnectError("fail"))
            mock_client_builder.return_value = mock_client

            result = await engine.bench("http://example.com", iterations=3)

        assert result.requests_completed == 0
        assert result.requests_failed == 3

    @pytest.mark.asyncio
    async def test_bench_with_http_errors(self) -> None:
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 500

        engine = FluxionEngine(verify_tls=False)

        with patch.object(engine, "_build_client") as mock_client_builder:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client_builder.return_value = mock_client

            result = await engine.bench("http://example.com", iterations=2)

        assert result.requests_completed == 0
        assert result.requests_failed == 2


class TestEngineHelpers:
    def test_filename_from_url(self) -> None:
        assert FluxionEngine._filename_from_url("https://example.com/file.tar.gz") == "file.tar.gz"
        assert FluxionEngine._filename_from_url("https://example.com/") == "download"
        assert FluxionEngine._filename_from_url("https://example.com") == "download"
        assert FluxionEngine._filename_from_url("https://example.com/a/b/c.zip") == "c.zip"

    def test_detect_protocol(self) -> None:
        engine = FluxionEngine()
        assert engine._detect_protocol(ProbeResult(url="", http_version="HTTP/2")) == Protocol.HTTP2
        assert engine._detect_protocol(ProbeResult(url="", http_version="h3")) == Protocol.HTTP3
        assert engine._detect_protocol(ProbeResult(url="", http_version="HTTP/1.1")) == Protocol.HTTP1

    def test_notify_with_callback(self) -> None:
        calls = []
        FluxionEngine._notify(lambda s: calls.append(s), MagicMock())
        assert len(calls) == 1

    def test_notify_without_callback(self) -> None:
        FluxionEngine._notify(None, MagicMock())  # Should not raise


class TestEngineInit:
    def test_default_init(self) -> None:
        engine = FluxionEngine()
        assert engine._max_connections == 8
        assert engine._timeout == 30.0
        assert engine._verify_tls is True

    def test_custom_init(self) -> None:
        engine = FluxionEngine(
            max_connections=16,
            timeout=60.0,
            verify_tls=False,
            proxy="http://proxy:8080",
        )
        assert engine._max_connections == 16
        assert engine._timeout == 60.0
        assert engine._verify_tls is False
        assert engine._proxies == {"http://": "http://proxy:8080", "https://": "http://proxy:8080"}

    def test_build_client(self) -> None:
        engine = FluxionEngine()
        client = engine._build_client()
        assert isinstance(client, httpx.AsyncClient)

    def test_build_client_extra_headers(self) -> None:
        engine = FluxionEngine()
        extra = {"X-Custom": "value", "User-Agent": "Override/1.0"}
        client = engine._build_client(extra_headers=extra)
        assert isinstance(client, httpx.AsyncClient)
        # The extra headers should be merged with base headers
        assert client.headers["x-custom"] == "value"
        assert client.headers["user-agent"] == "Override/1.0"

    def test_user_agent_from_init(self) -> None:
        engine = FluxionEngine(user_agent="MyAgent/2.0")
        client = engine._build_client()
        assert client.headers["user-agent"] == "MyAgent/2.0"


class TestEngineStealthHeaders:
    def test_resolve_stealth_headers_empty(self) -> None:
        request = FetchRequest(url="https://example.com/file")
        headers = FluxionEngine._resolve_stealth_headers(request)
        assert headers == {}

    def test_resolve_stealth_headers_with_profile(self) -> None:
        request = FetchRequest(
            url="https://example.com/file",
            browser_profile="chrome",
        )
        headers = FluxionEngine._resolve_stealth_headers(request)
        assert "User-Agent" in headers
        assert "Chrome" in headers["User-Agent"]
        assert "Sec-Fetch-Dest" in headers

    def test_resolve_stealth_headers_with_custom(self) -> None:
        request = FetchRequest(
            url="https://example.com/file",
            headers={"Authorization": "Bearer token123"},
        )
        headers = FluxionEngine._resolve_stealth_headers(request)
        assert headers["Authorization"] == "Bearer token123"

    def test_resolve_stealth_headers_with_cookies(self) -> None:
        request = FetchRequest(
            url="https://example.com/file",
            cookies={"session": "abc"},
        )
        headers = FluxionEngine._resolve_stealth_headers(request)
        assert headers["Cookie"] == "session=abc"

    def test_resolve_stealth_headers_with_referer(self) -> None:
        request = FetchRequest(
            url="https://example.com/file",
            referer="https://google.com",
        )
        headers = FluxionEngine._resolve_stealth_headers(request)
        assert headers["Referer"] == "https://google.com"


class TestEngineRetry:
    @pytest.mark.asyncio
    async def test_stream_download_retries_429(self, tmp_path: Path) -> None:
        """429 should be retried, then succeed on second attempt."""
        engine = FluxionEngine(verify_tls=False)
        output = tmp_path / "out.bin"

        class FakeResponse:
            def __init__(self, status: int, content: bytes) -> None:
                self.status_code = status
                self.reason_phrase = "Too Many Requests" if status == 429 else "OK"
                self.headers = {"content-length": str(len(content))}
                self._content = content

            async def aiter_bytes(self, chunk_size: int = 65536):
                yield self._content

        call_count = 0

        class FakeStreamCtx:
            async def __aenter__(self_ctx):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return FakeResponse(429, b"")
                return FakeResponse(200, b"hello")

            async def __aexit__(self_ctx, *args):
                pass

        with patch.object(engine, "_build_client") as mock_builder:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.stream = MagicMock(side_effect=lambda *a, **kw: FakeStreamCtx())
            mock_builder.return_value = mock_client

            from fluxion.models import TransferStats, TransferPhase

            stats = TransferStats(phase=TransferPhase.STREAM)
            request = FetchRequest(url="http://example.com/file", max_retries=3)

            result = await engine._stream_download(
                request, output, Protocol.HTTP1, stats, None
            )

        assert result == 5

    @pytest.mark.asyncio
    async def test_stream_download_no_retry_404(self, tmp_path: Path) -> None:
        """404 is fatal and should NOT be retried."""
        engine = FluxionEngine(verify_tls=False)
        output = tmp_path / "out.bin"

        class FakeResponse:
            status_code = 404
            reason_phrase = "Not Found"
            headers: dict[str, str] = {}

        class FakeStreamCtx:
            async def __aenter__(self_ctx):
                return FakeResponse()

            async def __aexit__(self_ctx, *args):
                pass

        with patch.object(engine, "_build_client") as mock_builder:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.stream = MagicMock(return_value=FakeStreamCtx())
            mock_builder.return_value = mock_client

            from fluxion.models import TransferStats, TransferPhase

            stats = TransferStats(phase=TransferPhase.STREAM)
            request = FetchRequest(url="http://example.com/file", max_retries=3)

            with pytest.raises(NetworkError, match="HTTP 404"):
                await engine._stream_download(
                    request, output, Protocol.HTTP1, stats, None
                )

        # Should only have been called once (no retry for 404)
        assert mock_client.stream.call_count == 1


class TestEngineProtocolDispatch:
    @pytest.mark.asyncio
    async def test_ftp_dispatch(self) -> None:
        engine = FluxionEngine(verify_tls=False)
        request = FetchRequest(url="ftp://example.com/file.bin")

        with patch("fluxion.protocols.ftp.FTPHandler") as MockFTP:
            mock_handler = AsyncMock()
            mock_handler.download = AsyncMock(return_value=1024)
            MockFTP.return_value = mock_handler

            with patch.object(IntegrityVerifier, "compute_sha256", return_value="abc123"):
                result = await engine.fetch(request)

            assert result.protocol_used == Protocol.FTP
            assert result.bytes_downloaded == 1024

    @pytest.mark.asyncio
    async def test_sftp_dispatch(self) -> None:
        engine = FluxionEngine(verify_tls=False)
        request = FetchRequest(url="sftp://example.com/file.bin")

        with patch("fluxion.protocols.sftp.SFTPHandler") as MockSFTP:
            mock_handler = AsyncMock()
            mock_handler.download_sftp = AsyncMock(return_value=2048)
            MockSFTP.return_value = mock_handler

            with patch.object(IntegrityVerifier, "compute_sha256", return_value="def456"):
                result = await engine.fetch(request)

            assert result.protocol_used == Protocol.SFTP
            assert result.bytes_downloaded == 2048

    @pytest.mark.asyncio
    async def test_scp_dispatch(self) -> None:
        engine = FluxionEngine(verify_tls=False)
        request = FetchRequest(url="scp://example.com/file.bin")

        with patch("fluxion.protocols.sftp.SFTPHandler") as MockSFTP:
            mock_handler = AsyncMock()
            mock_handler.download_scp = AsyncMock(return_value=512)
            MockSFTP.return_value = mock_handler

            with patch.object(IntegrityVerifier, "compute_sha256", return_value="ghi789"):
                result = await engine.fetch(request)

            assert result.protocol_used == Protocol.SCP
            assert result.bytes_downloaded == 512


class TestEngineResumeFallback:
    @pytest.mark.asyncio
    async def test_resume_falls_back_to_fresh_when_no_range(self, tmp_path: Path) -> None:
        """When resume=True but server lacks range support, fall back to fresh download."""
        engine = FluxionEngine(verify_tls=False)
        output = tmp_path / "partial.bin"
        output.write_bytes(b"partial data")

        mock_probe = ProbeResult(
            url="http://example.com/file",
            supports_range=False,
            content_length=1000,
        )

        with patch.object(engine, "probe", new_callable=AsyncMock, return_value=mock_probe):
            with patch.object(engine, "_stream_download", new_callable=AsyncMock, return_value=1000) as mock_stream:
                request = FetchRequest(
                    url="http://example.com/file",
                    output=output,
                    resume=True,
                )
                result = await engine.fetch(request)
                # Should have proceeded with download, not raised ResumeError
                mock_stream.assert_called_once()
                assert result.bytes_downloaded == 1000


class TestEngineBenchThroughput:
    @pytest.mark.asyncio
    async def test_bench_populates_throughput(self) -> None:
        mock_head_response = MagicMock()
        mock_head_response.is_success = True

        mock_get_response = MagicMock()
        mock_get_response.content = b"x" * 1024

        engine = FluxionEngine(verify_tls=False)

        with patch.object(engine, "_build_client") as mock_builder:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.head = AsyncMock(return_value=mock_head_response)
            mock_client.get = AsyncMock(return_value=mock_get_response)
            mock_builder.return_value = mock_client

            result = await engine.bench("http://example.com", iterations=2)

        assert result.requests_completed == 2
        assert result.throughput_mbps >= 0
