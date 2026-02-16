<div align="center">

<!-- HEADER -->
<br>

```
 ███████╗██╗     ██╗   ██╗██╗  ██╗██╗ ██████╗ ███╗   ██╗
 ██╔════╝██║     ██║   ██║╚██╗██╔╝██║██╔═══██╗████╗  ██║
 █████╗  ██║     ██║   ██║ ╚███╔╝ ██║██║   ██║██╔██╗ ██║
 ██╔══╝  ██║     ██║   ██║ ██╔██╗ ██║██║   ██║██║╚██╗██║
 ██║     ███████╗╚██████╔╝██╔╝ ██╗██║╚██████╔╝██║ ╚████║
 ╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
```

### ⟡ The Intelligent Network Command Engine

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-00D4AA?style=for-the-badge)](LICENSE)
[![Version](https://img.shields.io/badge/v1.0.0-Quantum-7B2FBE?style=for-the-badge)]()
[![HTTP2](https://img.shields.io/badge/HTTP/2-Enabled-00BFFF?style=for-the-badge)]()
[![HTTP3](https://img.shields.io/badge/HTTP/3-QUIC-FF6B6B?style=for-the-badge)]()

<br>

**Fluxion** is a next-generation, protocol-aware download engine built for speed, security, and intelligence.
Adaptive parallel transport. Real-time network telemetry. TLS deep inspection. Browser-grade stealth.
All from your terminal.

<br>

[Installation](#-installation) · [Commands](#-commands) · [Features](#-features) · [Configuration](#%EF%B8%8F-configuration) · [Plugins](#-plugins) · [Architecture](#-architecture)

<br>

---

</div>

<br>

## ⚡ Quick Start

```bash
pip install fluxion        # Install
fluxion init               # Initialize environment
fluxion fetch <url>        # Download anything
```

<br>

## 📦 Installation

### From PyPI

```bash
# Standard install
pip install fluxion

# With browser cookie extraction & stealth capabilities
pip install 'fluxion[stealth]'

# Development (includes linters, test suite, type checking)
pip install 'fluxion[dev]'
```

### Run as Module

```bash
python -m fluxion
```

### Platform Packages

| Platform | Format | Location |
|:---------|:-------|:---------|
| 🪟 Windows | WiX Installer | `packaging/windows/` |
| 🐧 Debian/Ubuntu | `.deb` | `packaging/deb/` |
| 🎩 Fedora/RHEL | `.rpm` | `packaging/rpm/` |
| 🍎 macOS | Homebrew | `packaging/homebrew/` |

### Post-Install

```bash
fluxion init     # Detect OS, install system deps, verify TLS chain
fluxion doctor   # Run full diagnostic check
```

<br>

## 🛸 Commands

Fluxion ships with **11 built-in commands**, each designed for a specific network operation.

<br>

### `fetch` — Intelligent Parallel Download

The core command. Downloads files using adaptive multi-connection transport with automatic protocol negotiation.

```bash
fluxion fetch https://releases.example.com/v2.0/package.tar.gz
```

```bash
# 16 parallel streams, custom output, SHA-256 verification
fluxion fetch https://cdn.example.com/data.zip \
  -o ./data.zip \
  -c 16 \
  --sha256 e3b0c44298fc1c149afbf4c8996fb924...

# Browser impersonation with live cookies
fluxion fetch https://protected.site/asset.bin \
  --browser-profile chrome \
  --browser-cookies firefox

# Custom headers, proxy, referer
fluxion fetch https://api.example.com/export \
  -H "Authorization: Bearer tok_abc123" \
  -H "X-Request-ID: flx-001" \
  --proxy http://proxy.corp:8080 \
  --referer https://api.example.com/dashboard
```

<details>
<summary><b>All Options</b></summary>

| Flag | Short | Default | Description |
|:-----|:------|:--------|:------------|
| `--output` | `-o` | Auto-derived | Output file path |
| `--connections` | `-c` | `8` | Max parallel connections |
| `--no-resume` | | `False` | Disable resume support |
| `--no-verify` | | `False` | Skip TLS certificate verification |
| `--timeout` | | `30.0` | Request timeout (seconds) |
| `--proxy` | | | Proxy URL |
| `--sha256` | | | Expected SHA-256 hash |
| `--header` | `-H` | | Custom header (repeatable) |
| `--cookie` | | | Cookie string (repeatable) |
| `--cookie-file` | | | Netscape or JSON cookie file |
| `--browser-cookies` | | | Import from browser (`chrome`/`firefox`/`edge`/`safari`) |
| `--browser-profile` | | | Impersonate browser (`chrome`/`firefox`/`edge`/`safari`) |
| `--referer` | | | Referer URL |
| `--minimal` | | | Single-line progress |
| `--plain` | | | No styling |
| `--json` | | | Machine-readable JSON output |
| `--quiet` | | | Suppress all output |

</details>

<br>

### `stream` — Pipe Content to Stdout

Stream raw bytes directly to stdout. Perfect for piping into other tools.

```bash
fluxion stream https://api.example.com/feed.json | jq '.data[]'
fluxion stream https://logs.example.com/latest.log | grep ERROR
```

<br>

### `probe` — Network Intelligence Scan

Perform a deep reconnaissance probe on any URL. Returns protocol details, TLS state, server fingerprint, latency, and range support.

```bash
fluxion probe https://cdn.example.com/asset.bin
```

```
⟡ NETWORK INTELLIGENCE ──────────────────────────
  HOST           cdn.example.com
  RESOLVED       104.18.25.43
  HTTP           HTTP/2
  SERVER         cloudflare
  LATENCY        23.4 ms
  TLS            TLSv1.3
  CIPHER         TLS_AES_256_GCM_SHA384
  CERT ISSUER    Let's Encrypt
  CERT EXPIRY    2026-05-14
  RANGE          YES
  SIZE           1.24 GiB
  TYPE           application/octet-stream
```

<br>

### `bench` — Performance Benchmarking

Measure real-world network performance with statistical analysis.

```bash
fluxion bench https://cdn.example.com/test-payload -n 20
```

Reports: min/max/avg latency, P50/P95/P99 percentiles, jitter, stability score (0.0–1.0), and throughput in Mbps.

<br>

### `mirror` — Fastest Mirror Selection

Provide multiple mirror URLs. Fluxion probes all of them in parallel, selects the lowest-latency endpoint, and fetches from it.

```bash
fluxion mirror \
  https://mirror1.example.com/release.iso \
  https://mirror2.example.com/release.iso \
  https://mirror3.example.com/release.iso \
  -o release.iso
```

<br>

### `secure` — TLS Deep Inspection

Full certificate and cipher analysis for any HTTPS endpoint.

```bash
fluxion secure https://bank.example.com
```

```
⟡ TLS SECURITY ──────────────────────────────────
  SUBJECT        bank.example.com
  ISSUER         DigiCert Global G2
  TLS            TLSv1.3
  CIPHER         TLS_AES_256_GCM_SHA384
  SERIAL         0A:1B:2C:3D:4E:5F...
  VALID FROM     2025-01-15
  VALID UNTIL    2026-01-15
  SHA-256        a1b2c3d4e5f6...
  SAN            bank.example.com, *.bank.example.com
```

<br>

### `init` — Environment Setup

Detects your OS, installs system dependencies (OpenSSL, build tools), creates config directories, and verifies TLS chains.

```bash
fluxion init
```

Supports: `apt`, `dnf`, `pacman`, `zypper`, `apk`, `emerge`, `nix-env`, `brew`, `choco`, `winget`

<br>

### `doctor` — Diagnostic Health Check

```bash
fluxion doctor
```

Checks Python version, platform info, OpenSSL, all required and optional packages, and config directory integrity.

<br>

### `config` — Configuration Management

```bash
fluxion config                          # View current config
fluxion config --set max_connections=16 # Set a value
fluxion config --set proxy=socks5://localhost:1080
```

<br>

### `plugin` — Plugin Management

```bash
fluxion plugin list              # List installed plugins
fluxion plugin install s3        # Install from PyPI
fluxion plugin remove s3         # Uninstall
```

<br>

### `version` — Version Info

```bash
fluxion version
# ⟡ Fluxion v1.0.0 [Quantum]
```

<br>

## 🔮 Features

### ⚡ Adaptive Parallel Transport

Fluxion doesn't just split files into chunks — it **learns** and adapts in real-time.

| Component | Behavior |
|:----------|:---------|
| **Adaptive Chunker** | Dynamic chunk sizing from 256 KiB to 16 MiB. Uses EMA throughput tracking to double chunk size when speed increases and halve when it drops. |
| **Connection Optimizer** | Scales concurrency from 1 to 32 connections. Monitors throughput every 2s — ramps up on improvement, backs off on degradation. Instantly halves on HTTP 429. |
| **Bandwidth Estimator** | 30-sample sliding window with EMA smoothing. Real-time speed, average speed, and ETA calculation. |
| **Parallel Scheduler** | Semaphore-based async orchestration. Feeds live metrics back to chunker and optimizer for continuous tuning. |
| **Retry Classifier** | Categorizes errors as retryable, fatal, or backoff. Exponential backoff capped at 30s. Distinguishes timeouts, connection errors, DNS failures, and TLS errors. |

**Download Modes:**

| Mode | When |
|:-----|:-----|
| `PARALLEL` | Server supports range requests + file is large enough |
| `SINGLE` | Fallback for non-range servers |
| `STREAM` | Direct stdout pipe (`stream` command) |
| `MIRROR` | Multi-origin fastest-first (`mirror` command) |

<br>

### 🔒 Security Layer

| Feature | Details |
|:--------|:--------|
| **TLS Deep Inspection** | Raw socket-level TLS analysis independent of HTTP client. Extracts version, cipher, cert chain, SANs, fingerprint. |
| **Certificate Pinning** | Pin expected SHA-256 fingerprints per hostname. Raises `SecurityError` on mismatch. |
| **Expiry Monitoring** | Warns when certificates expire within 30 days. |
| **Integrity Verification** | SHA-256 checksum of downloaded files. Incremental hashing during transfer. Block-read (256 KiB) for efficiency. |
| **Secure Temp Files** | `SecureTempFile` context manager with `chmod 0o600`. Auto-cleaned on exit. |
| **Proxy Detection** | Auto-reads `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` env vars. Manual override via `--proxy`. |

<br>

### 🥷 Stealth & Browser Impersonation

Bypass bot detection and access protected resources with full browser-grade request signatures.

**Built-in Profiles:**

| Profile | Identity |
|:--------|:---------|
| `chrome` | Chrome 131 — Windows x64 |
| `firefox` | Firefox 134 — Windows x64 |
| `edge` | Edge 131 — Windows x64 |
| `safari` | Safari 18.2 — macOS 14.7 |

Each profile includes accurate `User-Agent`, `Accept`, `Accept-Language`, `Accept-Encoding`, `Sec-Fetch-*`, and `Sec-Ch-Ua-*` headers.

**Cookie System:**

```bash
# Inline cookies
fluxion fetch <url> --cookie "session=abc123; token=xyz"

# From Netscape cookie file or JSON array
fluxion fetch <url> --cookie-file cookies.txt

# Live extraction from installed browser (requires fluxion[stealth])
fluxion fetch <url> --browser-cookies chrome
```

<br>

### 🌐 Multi-Protocol Engine

| Protocol | Transport | Notes |
|:---------|:----------|:------|
| HTTP/1.1 | httpx | Automatic fallback |
| HTTP/2 | httpx + h2 | Default, multiplexed streams |
| HTTP/3 | aioquic | QUIC-based, 0-RTT capable |
| FTP | aioftp | Anonymous and authenticated |
| SFTP | asyncssh | Password and key authentication |
| SCP | asyncssh | Secure remote copy |

Protocol is auto-negotiated from the probe response. Extensible via the plugin system.

<br>

### 🖥️ Quantum HUD

A responsive terminal interface that adapts to your terminal size with four layout modes.

| Width | Mode | Rendering |
|:------|:-----|:----------|
| < 60 | `MINIMAL` | Single-line output |
| 60–90 | `COMPACT` | Abbreviated panels |
| 90–130 | `STANDARD` | Full panels with codename |
| 130+ | `FULL` | Double-line bordered header |

**Live Transfer Display:**

```
╔══════════════════════════════════════════════════════╗
║  ⟡ FLUXION v1.0.0 [Quantum]                         ║
╚══════════════════════════════════════════════════════╝
⟡ FLUXION TRANSFER ──────────────────────────────────
  TARGET     https://cdn.example.com/release-v2.tar.gz
  MODE       PARALLEL
  STATUS     ▶ STREAM
  SPEED      124.7 MiB/s
  PROGRESS   ██████████████████░░░░░░  74.2%
  SIZE       953.1 MiB / 1.24 GiB
  ETA        00:02:13
  STREAMS    12
```

**Output Modes:**

| Mode | Flag | Use Case |
|:-----|:-----|:---------|
| Default | — | Full Rich panels with live updates |
| Minimal | `--minimal` | Single-line in-place progress |
| Plain | `--plain` | No styling, pipe-safe |
| JSON | `--json` | Machine-readable, scriptable |
| Quiet | `--quiet` | Exit code only |

**Windows Terminal Support:**
Full Unicode and ANSI color support for Windows Terminal, ConEmu, VS Code, and mintty. Automatic ASCII fallback for legacy terminals.

<br>

## ⚙️ Configuration

Config is stored at `~/.fluxion/config.json` and managed via `fluxion config`.

| Key | Type | Default | Description |
|:----|:-----|:--------|:------------|
| `default_output_dir` | path | `cwd` | Default download directory |
| `max_connections` | int | `8` | Parallel connection limit |
| `default_timeout` | float | `30.0` | Request timeout (seconds) |
| `verify_tls` | bool | `true` | TLS certificate verification |
| `proxy` | string | `null` | Default proxy URL |
| `user_agent` | string | Chrome 131 | Default User-Agent |
| `enable_http3` | bool | `true` | HTTP/3 QUIC support |
| `plugin_dirs` | list | `[]` | Additional plugin directories |
| `theme` | string | `"quantum"` | UI theme |
| `default_browser_profile` | string | `null` | Default impersonation profile |

```bash
fluxion config                                 # View all
fluxion config --set max_connections=32        # Tune parallelism
fluxion config --set enable_http3=false        # Disable QUIC
fluxion config --set default_browser_profile=firefox
```

<br>

## 🧩 Plugins

Fluxion's plugin system allows extending protocol support and adding custom commands.

### Plugin Types

| Type | Base Class | Purpose |
|:-----|:-----------|:--------|
| **Protocol** | `ProtocolPlugin` | Handle new URL schemes (e.g., `s3://`, `magnet:`) |
| **Command** | `CommandPlugin` | Add new CLI commands |

### Creating a Plugin

```python
from fluxion.plugins.base import ProtocolPlugin
from fluxion.models import PluginMeta
from pathlib import Path


class S3Plugin(ProtocolPlugin):
    def metadata(self) -> PluginMeta:
        return PluginMeta(
            name="s3",
            version="1.0.0",
            description="Amazon S3 protocol support",
            protocols=["s3"],
        )

    async def download(self, url: str, output: Path, **kwargs) -> int:
        # ... S3 download implementation ...
        return bytes_downloaded


def create_plugin() -> S3Plugin:
    return S3Plugin()
```

### Plugin Convention

- **PyPI package**: `fluxion-plugin-<name>`
- **Module name**: `fluxion_plugin_<name>`
- **Factory**: Must export `create_plugin()` returning a `FluxionPlugin` instance
- **Registry**: `~/.fluxion/plugins.json`
- **Directory**: `~/.fluxion/plugins/`

### Lifecycle Hooks

| Hook | When |
|:-----|:-----|
| `on_load()` | Plugin is loaded into the engine |
| `on_unload()` | Plugin is removed or engine shuts down |

<br>

## 🏗️ Architecture

```
fluxion/
├── cli/
│   └── app.py                 # Typer CLI — 11 commands
├── core/
│   └── engine.py              # FluxionEngine — probe, bench, fetch, stream, mirror
├── hud/
│   ├── layout.py              # Terminal detection, responsive layout modes
│   ├── panels.py              # Rich panel renderers (header, progress, probe, etc.)
│   └── renderer.py            # Live display lifecycle (Rich Live context)
├── performance/
│   ├── bandwidth.py           # EMA sliding-window bandwidth estimator
│   ├── chunker.py             # Adaptive chunk sizing (256 KiB – 16 MiB)
│   ├── optimizer.py           # Dynamic concurrency scaling (1–32)
│   ├── retry.py               # Error classification + exponential backoff
│   └── scheduler.py           # Async semaphore-based parallel orchestration
├── security/
│   ├── integrity.py           # SHA-256 verification, secure temp files
│   ├── proxy.py               # Environment proxy detection
│   └── tls.py                 # Raw socket TLS inspection, cert pinning
├── stealth/
│   ├── context.py             # Header assembly from all stealth sources
│   ├── cookies.py             # Cookie jar (raw, file, browser import)
│   └── profiles.py            # Browser fingerprint profiles
├── protocols/
│   ├── ftp.py                 # Async FTP handler
│   ├── sftp.py                # SFTP + SCP handler
│   └── quic.py                # HTTP/3 over QUIC handler
├── plugins/
│   ├── base.py                # Plugin abstract base classes
│   └── manager.py             # Install, remove, load, dispatch
├── installer/
│   ├── config.py              # Config load/save/show
│   ├── doctor.py              # Diagnostic checks
│   ├── privilege.py           # Root detection, privilege escalation
│   └── setup.py               # Full init sequence
├── platform/
│   └── detect.py              # OS/distro/arch detection
├── models.py                  # Pydantic models and enums
├── exceptions.py              # Exception hierarchy
├── __init__.py                # Version: 1.0.0 [Quantum]
└── __main__.py                # python -m fluxion
```

### Data Flow — `fetch`

```
URL ──▶ CLI Parser ──▶ FetchRequest Model
                            │
                            ▼
                      FluxionEngine
                            │
                    ┌───────┴───────┐
                    ▼               ▼
              TLS Inspector    HEAD Probe
                    │               │
                    └───────┬───────┘
                            ▼
                      ProbeResult
                            │
                   ┌────────┴─────────┐
                   ▼                  ▼
             Range Support?     Single Stream
                   │
                   ▼
           ParallelScheduler
            ┌──────┼──────┐
            ▼      ▼      ▼
         Chunk   Chunk   Chunk      ◀── AdaptiveChunker
            │      │      │             ConnectionOptimizer
            ▼      ▼      ▼             RetryClassifier
         BandwidthEstimator             BandwidthEstimator
                   │
                   ▼
          IntegrityVerifier ──▶ SHA-256
                   │
                   ▼
             FetchResult ──▶ HUD Panel
```

<br>

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=fluxion --cov-report=term-missing

# Specific module
pytest tests/unit/test_engine.py
```

| Metric | Value |
|:-------|:------|
| Unit tests | 174 |
| Coverage | 57%+ |
| Async framework | `pytest-asyncio` (auto mode) |
| HTTP mocking | `respx` |
| Test location | `tests/unit/` |

<br>

## 🌍 Platform Support

| Platform | Status | Notes |
|:---------|:-------|:------|
| 🐧 Linux | Full | All major distros (Ubuntu, Fedora, Arch, Alpine, Gentoo, NixOS, Void, etc.) |
| 🍎 macOS | Full | Homebrew integration |
| 🪟 Windows | Full | Unicode support for modern terminals, ASCII fallback for legacy |
| 🐧 WSL | Full | Auto-detected via `/proc/version` |
| 😈 BSD | Full | FreeBSD, OpenBSD, NetBSD |

**Architectures:** x86_64, aarch64 (ARM64), armv7l

<br>

## 📚 Dependencies

| Package | Purpose |
|:--------|:--------|
| [httpx](https://www.python-httpx.org/) | Async HTTP client with HTTP/2 |
| [aioquic](https://github.com/aiortc/aioquic) | HTTP/3 over QUIC |
| [rich](https://rich.readthedocs.io/) | Terminal UI rendering |
| [typer](https://typer.tiangolo.com/) | CLI framework |
| [pydantic](https://docs.pydantic.dev/) | Data validation and models |
| [anyio](https://anyio.readthedocs.io/) | Async runtime abstraction |
| [asyncssh](https://asyncssh.readthedocs.io/) | SFTP/SCP protocol |
| [aioftp](https://aioftp.readthedocs.io/) | FTP protocol |
| [aiofiles](https://github.com/Tinche/aiofiles) | Async file I/O |
| [certifi](https://github.com/certifi/python-certifi) | TLS CA certificates |

<br>

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

<br>

---

<div align="center">

```
 ⟡ Built for those who demand more from their terminal.
```

**Fluxion** · v1.0.0 [Quantum] · MIT License

</div>
