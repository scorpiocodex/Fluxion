"""Pydantic models and data structures used across Fluxion."""

from __future__ import annotations

import enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Protocol(str, enum.Enum):
    HTTP1 = "HTTP/1.1"
    HTTP2 = "HTTP/2"
    HTTP3 = "HTTP/3"
    FTP = "FTP"
    SFTP = "SFTP"
    SCP = "SCP"


class TransferPhase(str, enum.Enum):
    RESOLVING = "RESOLVING"
    CONNECTING = "CONNECTING"
    TLS = "TLS"
    PROTOCOL_LOCK = "PROTOCOL LOCK"
    STREAM = "STREAM"
    VERIFY = "VERIFY"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


class OutputMode(str, enum.Enum):
    DEFAULT = "default"
    MINIMAL = "minimal"
    PLAIN = "plain"
    JSON = "json"
    QUIET = "quiet"


class FluxMode(str, enum.Enum):
    SMART = "SMART"
    PARALLEL = "PARALLEL"
    STREAM = "STREAM"
    SINGLE = "SINGLE"
    MIRROR = "MIRROR"


# ---------------------------------------------------------------------------
# Platform
# ---------------------------------------------------------------------------


class DistroInfo(BaseModel):
    """Detected operating system / distribution information."""

    name: str
    family: str
    version: str
    package_manager: str
    arch: str


# ---------------------------------------------------------------------------
# Network / Transfer
# ---------------------------------------------------------------------------


class TransferStats(BaseModel):
    """Live transfer statistics."""

    bytes_downloaded: int = 0
    bytes_total: int | None = None
    speed_bytes_per_sec: float = 0.0
    elapsed_seconds: float = 0.0
    eta_seconds: float | None = None
    active_connections: int = 0
    phase: TransferPhase = TransferPhase.RESOLVING
    flux_mode: FluxMode = FluxMode.SMART


class ProbeResult(BaseModel):
    """Result of a network probe."""

    url: str
    resolved_ip: str = ""
    tls_version: str = ""
    tls_cipher: str = ""
    certificate_issuer: str = ""
    certificate_expiry: str = ""
    http_version: str = ""
    server: str = ""
    supports_range: bool = False
    content_length: int | None = None
    content_type: str = ""
    latency_ms: float = 0.0
    headers: dict[str, str] = Field(default_factory=dict)


class BenchResult(BaseModel):
    """Result of a performance benchmark."""

    url: str
    latency_min_ms: float = 0.0
    latency_max_ms: float = 0.0
    latency_avg_ms: float = 0.0
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_p99_ms: float = 0.0
    jitter_ms: float = 0.0
    throughput_mbps: float = 0.0
    stability_score: float = 0.0  # 0.0 - 1.0
    requests_completed: int = 0
    requests_failed: int = 0


class FetchRequest(BaseModel):
    """Parameters for a fetch operation."""

    url: str
    output: Path | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    max_connections: int = 8
    chunk_size: int = 1024 * 1024  # 1 MiB
    resume: bool = True
    verify_tls: bool = True
    timeout: float = 30.0
    max_retries: int = 3
    proxy: str | None = None
    protocol: Protocol | None = None
    flux_mode: FluxMode = FluxMode.SMART
    browser_profile: str | None = None
    cookies: dict[str, str] = Field(default_factory=dict)
    referer: str | None = None


class FetchResult(BaseModel):
    """Result of a completed fetch."""

    url: str
    output_path: Path
    bytes_downloaded: int
    elapsed_seconds: float
    speed_bytes_per_sec: float
    protocol_used: Protocol
    sha256: str = ""
    resumed: bool = False


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class FluxionConfig(BaseModel):
    """Persistent user configuration."""

    default_output_dir: Path = Field(default_factory=lambda: Path.cwd())
    max_connections: int = 8
    default_timeout: float = 30.0
    verify_tls: bool = True
    proxy: str | None = None
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
    enable_http3: bool = True
    plugin_dirs: list[Path] = Field(default_factory=list)
    theme: str = "quantum"
    default_browser_profile: str | None = None


# ---------------------------------------------------------------------------
# Plugin
# ---------------------------------------------------------------------------


class PluginMeta(BaseModel):
    """Metadata describing a loaded plugin."""

    name: str
    version: str
    description: str = ""
    author: str = ""
    protocols: list[str] = Field(default_factory=list)
    commands: list[str] = Field(default_factory=list)
    enabled: bool = True
    entry_point: str = ""
    config: dict[str, Any] = Field(default_factory=dict)
