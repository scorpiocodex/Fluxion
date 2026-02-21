"""Tests for Fluxion data models."""

from pathlib import Path

from fluxion.models import (
    BenchResult,
    DistroInfo,
    FetchRequest,
    FetchResult,
    FluxionConfig,
    FluxMode,
    OutputMode,
    PluginMeta,
    ProbeResult,
    Protocol,
    TransferPhase,
    TransferStats,
)


class TestDistroInfo:
    def test_creation(self) -> None:
        info = DistroInfo(
            name="ubuntu",
            family="debian",
            version="22.04",
            package_manager="apt",
            arch="x86_64",
        )
        assert info.name == "ubuntu"
        assert info.family == "debian"
        assert info.package_manager == "apt"

    def test_serialization(self) -> None:
        info = DistroInfo(
            name="arch",
            family="arch",
            version="rolling",
            package_manager="pacman",
            arch="aarch64",
        )
        data = info.model_dump()
        assert data["name"] == "arch"
        restored = DistroInfo.model_validate(data)
        assert restored == info


class TestTransferStats:
    def test_defaults(self) -> None:
        stats = TransferStats()
        assert stats.bytes_downloaded == 0
        assert stats.phase == TransferPhase.RESOLVING
        assert stats.flux_mode == FluxMode.SMART

    def test_update(self) -> None:
        stats = TransferStats(
            bytes_downloaded=1024,
            bytes_total=4096,
            speed_bytes_per_sec=512.0,
            phase=TransferPhase.STREAM,
        )
        assert stats.bytes_total == 4096


class TestFetchRequest:
    def test_defaults(self) -> None:
        req = FetchRequest(url="https://example.com/file.bin")
        assert req.max_connections == 8
        assert req.resume is True
        assert req.verify_tls is True

    def test_custom(self) -> None:
        req = FetchRequest(
            url="https://example.com/file.bin",
            output=Path("/tmp/out.bin"),
            max_connections=16,
            resume=False,
        )
        assert req.max_connections == 16
        assert req.output == Path("/tmp/out.bin")

    def test_stealth_field_defaults(self) -> None:
        req = FetchRequest(url="https://example.com/file.bin")
        assert req.browser_profile is None
        assert req.cookies == {}
        assert req.referer is None

    def test_stealth_fields_custom(self) -> None:
        req = FetchRequest(
            url="https://example.com/file.bin",
            browser_profile="chrome",
            cookies={"session": "abc"},
            referer="https://google.com",
        )
        assert req.browser_profile == "chrome"
        assert req.cookies == {"session": "abc"}
        assert req.referer == "https://google.com"


class TestProbeResult:
    def test_creation(self) -> None:
        result = ProbeResult(
            url="https://example.com",
            http_version="HTTP/2",
            latency_ms=42.5,
        )
        assert result.http_version == "HTTP/2"


class TestBenchResult:
    def test_stability(self) -> None:
        result = BenchResult(
            url="https://example.com",
            stability_score=0.95,
            requests_completed=10,
        )
        assert result.stability_score == 0.95


class TestFluxionConfig:
    def test_defaults(self) -> None:
        config = FluxionConfig()
        assert config.max_connections == 8
        assert config.verify_tls is True
        assert config.theme == "quantum"
        assert config.default_browser_profile is None

    def test_browser_profile_config(self) -> None:
        config = FluxionConfig(default_browser_profile="chrome")
        assert config.default_browser_profile == "chrome"


class TestPluginMeta:
    def test_creation(self) -> None:
        meta = PluginMeta(
            name="s3",
            version="1.0.0",
            protocols=["s3"],
            commands=["s3-sync"],
        )
        assert "s3" in meta.protocols


class TestFetchResult:
    def test_creation(self) -> None:
        result = FetchResult(
            url="https://example.com/file.bin",
            output_path=Path("/tmp/file.bin"),
            bytes_downloaded=4096,
            elapsed_seconds=2.0,
            speed_bytes_per_sec=2048.0,
            protocol_used=Protocol.HTTP2,
            sha256="abc123",
            resumed=True,
        )
        assert result.bytes_downloaded == 4096
        assert result.resumed is True
        assert result.sha256 == "abc123"

    def test_serialization(self) -> None:
        result = FetchResult(
            url="https://example.com/file.bin",
            output_path=Path("file.bin"),
            bytes_downloaded=1024,
            elapsed_seconds=1.0,
            speed_bytes_per_sec=1024.0,
            protocol_used=Protocol.HTTP1,
        )
        data = result.model_dump()
        assert data["url"] == "https://example.com/file.bin"
        assert data["protocol_used"] == "HTTP/1.1"


class TestEnums:
    def test_protocol_values(self) -> None:
        assert Protocol.HTTP1.value == "HTTP/1.1"
        assert Protocol.HTTP2.value == "HTTP/2"
        assert Protocol.HTTP3.value == "HTTP/3"
        assert Protocol.FTP.value == "FTP"
        assert Protocol.SFTP.value == "SFTP"
        assert Protocol.SCP.value == "SCP"

    def test_transfer_phase(self) -> None:
        assert TransferPhase.RESOLVING.value == "RESOLVING"
        assert TransferPhase.COMPLETE.value == "COMPLETE"
        assert TransferPhase.ERROR.value == "ERROR"

    def test_output_mode(self) -> None:
        assert OutputMode.DEFAULT.value == "default"
        assert OutputMode.JSON.value == "json"
        assert OutputMode.QUIET.value == "quiet"
        assert OutputMode.MINIMAL.value == "minimal"
        assert OutputMode.PLAIN.value == "plain"

    def test_flux_mode(self) -> None:
        assert FluxMode.SMART.value == "SMART"
        assert FluxMode.PARALLEL.value == "PARALLEL"
        assert FluxMode.STREAM.value == "STREAM"
        assert FluxMode.SINGLE.value == "SINGLE"
        assert FluxMode.MIRROR.value == "MIRROR"
