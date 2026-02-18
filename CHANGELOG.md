# Changelog

All notable changes to Fluxion are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — Quantum — 2026-02-18

### Initial Release

**Fluxion v1.0.0 [Quantum]** — The Intelligent Network Command Engine.

#### Commands (12 total)

| Command | Description |
|:--------|:------------|
| `fetch` | Adaptive multi-stream parallel download with protocol negotiation |
| `stream` | Pipe URL content to stdout |
| `probe` | Deep network reconnaissance scan |
| `bench` | Statistical latency and throughput benchmarking |
| `mirror` | Race mirrors, download from fastest endpoint |
| `secure` | TLS deep inspection and certificate analysis |
| `init` | Initialize environment and install dependencies |
| `doctor` | Diagnose installation and environment health |
| `config` | View or modify runtime configuration |
| `plugin` | Manage protocol and command plugins |
| `version` | Display version and system info |
| `help` | Sci-fi themed command intelligence database |

#### Core Engine

- FluxionEngine with probe, bench, fetch, stream, and mirror operations
- Automatic protocol negotiation (HTTP/1.1 → HTTP/2 → HTTP/3)
- HTTP range-request resume support

#### Adaptive Parallel Transport

- AdaptiveChunker: Dynamic chunk sizing 256 KiB – 16 MiB using EMA throughput tracking
- ConnectionOptimizer: Scales concurrency 1–32 connections with 2s monitoring intervals
- BandwidthEstimator: 30-sample sliding window with EMA smoothing
- ParallelScheduler: Semaphore-based async orchestration
- RetryClassifier: Categorizes errors with exponential backoff capped at 30s

#### Security Layer

- TLS Deep Inspection: Raw socket-level analysis
- Certificate Pinning: SHA-256 fingerprint verification per hostname
- Expiry Monitoring: 30-day warning threshold
- IntegrityVerifier: Incremental SHA-256 during transfer
- SecureTempFile: chmod 0o600 context manager with auto-cleanup
- Proxy Detection: Auto-reads environment variables

#### Stealth & Browser Impersonation

- Built-in profiles: Chrome 131, Firefox 134, Edge 131, Safari 18.2
- Cookie system: inline, Netscape/JSON file, live browser extraction
- StealthContext assembles full browser-grade request headers

#### Multi-Protocol Support

- HTTP/1.1 (httpx fallback), HTTP/2 (default), HTTP/3/QUIC (aioquic)
- FTP (aioftp), SFTP + SCP (asyncssh)

#### Quantum HUD

- Responsive layout: MINIMAL / COMPACT / STANDARD / FULL
- Live transfer display with progress bar, speed, ETA, stream count
- Output modes: Default, Minimal, Plain, JSON, Quiet
- Windows VT100 compatibility via Win32 API

#### Testing

- 174 unit tests with 57%+ coverage
- CI: Ubuntu, Windows, macOS x Python 3.11, 3.12, 3.13

---

[1.0.0]: https://github.com/scorpiocodex/Fluxion/releases/tag/v1.0.0
