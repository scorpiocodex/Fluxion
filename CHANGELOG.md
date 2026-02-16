# Changelog

All notable changes to Fluxion will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — Quantum

The inaugural release of Fluxion.

### Added

- **Core Engine** — Intelligent download engine with probe, bench, fetch, stream, and mirror operations
- **Adaptive Parallel Transport** — Dynamic chunk sizing (256 KiB – 16 MiB) with EMA-based throughput tracking
- **Connection Optimizer** — Real-time concurrency scaling from 1 to 32 connections
- **Bandwidth Estimator** — 30-sample sliding window with EMA smoothing for speed and ETA
- **Parallel Scheduler** — Async semaphore-based chunk orchestration with live metric feedback
- **Retry Classifier** — Intelligent error categorization with exponential backoff (capped at 30s)
- **Multi-Protocol Support** — HTTP/1.1, HTTP/2, HTTP/3 (QUIC), FTP, SFTP, SCP
- **TLS Deep Inspection** — Raw socket-level certificate analysis, cipher suite detection, expiry monitoring
- **Certificate Pinning** — SHA-256 fingerprint pinning per hostname
- **Integrity Verification** — SHA-256 checksum with incremental hashing during transfer
- **Browser Impersonation** — Chrome, Firefox, Edge, Safari profiles with full header signatures
- **Cookie System** — Inline, Netscape file, JSON file, and live browser cookie extraction
- **Plugin System** — Protocol and command plugin architecture with PyPI integration
- **Quantum HUD** — Responsive Rich terminal UI with 4 layout modes and live transfer panels
- **11 CLI Commands** — fetch, stream, probe, bench, mirror, secure, init, doctor, config, plugin, version
- **Cross-Platform** — Linux, macOS, Windows, WSL, BSD with full Unicode and ASCII fallback
- **Configuration** — JSON config at `~/.fluxion/config.json` with CLI management
- **Environment Setup** — Automated OS detection, dependency installation, TLS chain verification
- **Diagnostic System** — Full environment health check via `fluxion doctor`
