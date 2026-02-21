"""HUD panel rendering — header, progress, probe, bench, error, result panels."""

from __future__ import annotations

from rich.console import Console, Group
from rich.panel import Panel
from rich import box
from rich.table import Table
from rich.text import Text

from fluxion import __version__, __codename__
from fluxion.hud.layout import LayoutMode, detect_layout, get_terminal_width, supports_unicode
from fluxion.models import BenchResult, FetchResult, ProbeResult, TransferStats

# ── Quantum Color Palette ─────────────────────────────────────────────────

QUANTUM_BLUE = "bright_cyan"
QUANTUM_GREEN = "bright_green"
QUANTUM_YELLOW = "bright_yellow"
QUANTUM_RED = "bright_red"
QUANTUM_MAGENTA = "bright_magenta"
QUANTUM_DIM = "dim"
QUANTUM_WHITE = "bold white"

# ── Icon System ───────────────────────────────────────────────────────────

ICON_PRIMARY = "\u27e1"  # ⟡
ICON_ASCII = "*"

FLUX_ICON_UNICODE = "\u26a1"  # ⚡
FLUX_ICON_ASCII = "~"

_PHASE_ICONS_UNICODE: dict[str, str] = {
    "RESOLVING": "\u25c7",      # ◇
    "CONNECTING": "\u25c6",     # ◆
    "TLS": "\u25a3",            # ▣
    "PROTOCOL LOCK": "\u27d0",  # ⟐
    "STREAM": "\u25b6",         # ▶
    "VERIFY": "\u2713",         # ✓
    "COMPLETE": "\u2605",       # ★
    "ERROR": "\u2717",          # ✗
}

_PHASE_ICONS_ASCII: dict[str, str] = {
    "RESOLVING": ".",
    "CONNECTING": ">",
    "TLS": "#",
    "PROTOCOL LOCK": "=",
    "STREAM": ">",
    "VERIFY": "+",
    "COMPLETE": "*",
    "ERROR": "X",
}


def _icon() -> str:
    """Return the primary Fluxion icon, respecting terminal capability."""
    if supports_unicode():
        return ICON_PRIMARY
    return ICON_ASCII


def _flux_icon() -> str:
    return FLUX_ICON_UNICODE if supports_unicode() else FLUX_ICON_ASCII


def _phase_icon(phase: str) -> str:
    if supports_unicode():
        return _PHASE_ICONS_UNICODE.get(phase, ".")
    return _PHASE_ICONS_ASCII.get(phase, ".")


# ── Header ────────────────────────────────────────────────────────────────


def render_header(console: Console | None = None) -> Panel | Text:
    """Render the Fluxion branded header bar, responsive to terminal width."""
    layout = detect_layout()
    icon = _icon()

    if layout == LayoutMode.MINIMAL:
        return Text("")

    if layout == LayoutMode.COMPACT:
        header_text = Text()
        header_text.append(f" {icon} ", style=QUANTUM_BLUE)
        header_text.append("FLUXION", style=f"bold {QUANTUM_BLUE}")
        header_text.append(f"  v{__version__}", style=QUANTUM_DIM)
        return header_text

    if layout == LayoutMode.STANDARD:
        header_text = Text()
        header_text.append(f"  {icon}  ", style=QUANTUM_BLUE)
        header_text.append("FLUXION", style=f"bold {QUANTUM_BLUE}")
        header_text.append(f"  v{__version__}", style=QUANTUM_DIM)
        header_text.append(f"  [{__codename__}]", style=QUANTUM_DIM)
        return header_text

    # FULL mode: boxed header with visual identity
    width = get_terminal_width()
    inner = width - 4
    uni = supports_unicode()

    # Sleek sci-fi ascii art for FLUXION
    art = [
        r"  ███████╗██╗     ██╗   ██╗██╗  ██╗██╗ ██████╗ ███╗   ██╗  ",
        r"  ██╔════╝██║     ██║   ██║╚██╗██╔╝██║██╔═══██╗████╗  ██║  ",
        r"  █████╗  ██║     ██║   ██║ ╚███╔╝ ██║██║   ██║██╔██╗ ██║  ",
        r"  ██╔══╝  ██║     ██║   ██║ ██╔██╗ ██║██║   ██║██║╚██╗██║  ",
        r"  ██║     ███████╗╚██████╔╝██╔╝ ██╗██║╚██████╔╝██║ ╚████║  ",
        r"  ╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝  "
    ]

    subtitle = f"v{__version__} [{__codename__}] :: Intelligent Network Command Engine"

    header_text = Text()
    if uni:
        bar = "\u2550" * inner
        header_text.append(f"\u2554{bar}\u2557\n", style=QUANTUM_BLUE)
        for line in art:
            header_text.append("\u2551", style=QUANTUM_BLUE)
            header_text.append(line.center(inner), style=f"bold {QUANTUM_BLUE}")
            header_text.append("\u2551\n", style=QUANTUM_BLUE)
            
        header_text.append("\u2551", style=QUANTUM_BLUE)
        header_text.append(subtitle.center(inner), style=QUANTUM_DIM)
        header_text.append("\u2551\n", style=QUANTUM_BLUE)
        header_text.append(f"\u255a{bar}\u255d", style=QUANTUM_BLUE)
    else:
        bar = "=" * inner
        header_text.append(f"+{bar}+\n", style=QUANTUM_BLUE)
        for line in art:
            header_text.append("|", style=QUANTUM_BLUE)
            header_text.append(line.center(inner), style=f"bold {QUANTUM_BLUE}")
            header_text.append("|\n", style=QUANTUM_BLUE)
            
        header_text.append("|", style=QUANTUM_BLUE)
        header_text.append(subtitle.center(inner), style=QUANTUM_DIM)
        header_text.append("|\n", style=QUANTUM_BLUE)
        header_text.append(f"+{bar}+", style=QUANTUM_BLUE)
    return header_text


# ── Progress Panel ────────────────────────────────────────────────────────


def render_progress_panel(stats: TransferStats, url: str = "") -> Panel:
    """Render the live transfer HUD panel."""
    layout = detect_layout()
    table = Table.grid(padding=(0, 2))
    table.add_column(style=QUANTUM_DIM, min_width=12)
    table.add_column()

    icon = _icon()
    phase = stats.phase.value
    phase_ic = _phase_icon(phase)

    if url:
        table.add_row("TARGET", Text(url, style=QUANTUM_WHITE))

    table.add_row("MODE", Text(str(stats.flux_mode.value), style=QUANTUM_BLUE))
    table.add_row(
        "STATUS",
        Text(f"{phase_ic} {phase}", style=_phase_style(phase)),
    )

    speed = _format_speed(stats.speed_bytes_per_sec)
    table.add_row("SPEED", Text(speed, style=QUANTUM_GREEN))

    if stats.bytes_total and stats.bytes_total > 0:
        pct = (stats.bytes_downloaded / stats.bytes_total) * 100
        bar = _render_bar(pct, layout)
        size_str = f"{_format_bytes(stats.bytes_downloaded)} / {_format_bytes(stats.bytes_total)}"
        table.add_row("PROGRESS", Text(f"{bar}  {pct:.1f}%", style=QUANTUM_GREEN))
        table.add_row("SIZE", Text(size_str, style="white"))
    else:
        table.add_row("DOWNLOADED", Text(_format_bytes(stats.bytes_downloaded), style="white"))

    if stats.eta_seconds is not None and stats.eta_seconds > 0:
        table.add_row("ETA", Text(_format_time(stats.eta_seconds), style=QUANTUM_YELLOW))

    if stats.active_connections > 0:
        table.add_row("STREAMS", Text(str(stats.active_connections), style=QUANTUM_MAGENTA))

    return Panel(
        table,
        title=f"[{QUANTUM_BLUE}]{icon} FLUXION TRANSFER[/{QUANTUM_BLUE}]",
        border_style=QUANTUM_BLUE,
        box=box.HEAVY_EDGE,
        padding=(1, 2),
    )


# ── Probe Panel ───────────────────────────────────────────────────────────


def render_probe_panel(result: ProbeResult) -> Panel:
    """Render the network intelligence probe panel."""
    table = Table.grid(padding=(0, 2))
    table.add_column(style=QUANTUM_DIM, min_width=16)
    table.add_column()

    table.add_row("HOST", Text(result.url, style=QUANTUM_WHITE))
    if result.resolved_ip:
        table.add_row("RESOLVED IP", Text(result.resolved_ip, style="white"))
    table.add_row("HTTP VERSION", Text(result.http_version, style=QUANTUM_BLUE))
    table.add_row("SERVER", Text(result.server or "\u2014", style="white"))
    table.add_row("LATENCY", Text(f"{result.latency_ms:.1f} ms", style=QUANTUM_GREEN))

    if result.tls_version:
        table.add_row("TLS VERSION", Text(result.tls_version, style=QUANTUM_GREEN))
        table.add_row("TLS CIPHER", Text(result.tls_cipher or "\u2014", style="white"))
        table.add_row("CERT ISSUER", Text(result.certificate_issuer or "\u2014", style="white"))
        table.add_row(
            "CERT EXPIRY",
            Text(result.certificate_expiry or "\u2014", style=QUANTUM_YELLOW),
        )

    range_style = QUANTUM_GREEN if result.supports_range else QUANTUM_RED
    table.add_row(
        "RANGE SUPPORT",
        Text("YES" if result.supports_range else "NO", style=range_style),
    )

    if result.content_length is not None:
        table.add_row("CONTENT SIZE", Text(_format_bytes(result.content_length), style="white"))

    table.add_row("CONTENT TYPE", Text(result.content_type or "\u2014", style="white"))

    icon = _icon()
    return Panel(
        table,
        title=f"[{QUANTUM_BLUE}]{icon} NETWORK INTELLIGENCE[/{QUANTUM_BLUE}]",
        border_style=QUANTUM_BLUE,
        box=box.HEAVY_EDGE,
        padding=(1, 2),
    )


# ── Bench Panel ───────────────────────────────────────────────────────────


def render_bench_panel(result: BenchResult) -> Panel:
    """Render the performance benchmark panel."""
    table = Table.grid(padding=(0, 2))
    table.add_column(style=QUANTUM_DIM, min_width=16)
    table.add_column()

    table.add_row("TARGET", Text(result.url, style=QUANTUM_WHITE))
    req_style = QUANTUM_GREEN if result.requests_failed == 0 else QUANTUM_YELLOW
    table.add_row(
        "REQUESTS",
        Text(f"{result.requests_completed} OK / {result.requests_failed} FAIL", style=req_style),
    )
    table.add_row("LATENCY MIN", Text(f"{result.latency_min_ms:.2f} ms", style="white"))
    table.add_row("LATENCY MAX", Text(f"{result.latency_max_ms:.2f} ms", style="white"))
    table.add_row("LATENCY AVG", Text(f"{result.latency_avg_ms:.2f} ms", style=QUANTUM_GREEN))
    table.add_row("LATENCY P50", Text(f"{result.latency_p50_ms:.2f} ms", style="white"))
    table.add_row("LATENCY P95", Text(f"{result.latency_p95_ms:.2f} ms", style=QUANTUM_YELLOW))
    table.add_row("LATENCY P99", Text(f"{result.latency_p99_ms:.2f} ms", style=QUANTUM_RED))
    table.add_row("JITTER", Text(f"{result.jitter_ms:.2f} ms", style="white"))

    score = result.stability_score
    if score >= 0.9:
        stab_style, stab_label = QUANTUM_GREEN, "EXCELLENT"
    elif score >= 0.7:
        stab_style, stab_label = QUANTUM_GREEN, "GOOD"
    elif score >= 0.5:
        stab_style, stab_label = QUANTUM_YELLOW, "FAIR"
    else:
        stab_style, stab_label = QUANTUM_RED, "POOR"

    table.add_row("STABILITY", Text(f"{score:.3f} ({stab_label})", style=stab_style))

    if result.throughput_mbps > 0:
        tp = result.throughput_mbps
        if tp >= 1000:
            tp_text = f"{tp / 1000:.2f} Gbps"
        elif tp >= 1:
            tp_text = f"{tp:.2f} Mbps"
        else:
            tp_text = f"{tp * 1000:.1f} Kbps"
        table.add_row("THROUGHPUT", Text(tp_text, style=QUANTUM_GREEN))

    icon = _icon()
    return Panel(
        table,
        title=f"[{QUANTUM_BLUE}]{icon} PERFORMANCE BENCHMARK[/{QUANTUM_BLUE}]",
        border_style=QUANTUM_BLUE,
        box=box.HEAVY_EDGE,
        padding=(1, 2),
    )


# ── Result Panel ──────────────────────────────────────────────────────────


def render_result_panel(result: FetchResult) -> Panel:
    """Render a structured download result panel."""
    table = Table.grid(padding=(0, 2))
    table.add_column(style=QUANTUM_DIM, min_width=14)
    table.add_column()

    table.add_row("FILE", Text(str(result.output_path), style=QUANTUM_WHITE))
    table.add_row("URL", Text(result.url, style="white"))
    table.add_row("SIZE", Text(_format_bytes(result.bytes_downloaded), style=QUANTUM_GREEN))
    table.add_row(
        "SPEED",
        Text(_format_speed(result.speed_bytes_per_sec), style=QUANTUM_GREEN),
    )
    table.add_row("TIME", Text(_format_time(result.elapsed_seconds), style="white"))
    table.add_row("PROTOCOL", Text(result.protocol_used.value, style=QUANTUM_BLUE))
    if result.sha256:
        table.add_row("SHA-256", Text(result.sha256[:16] + "...", style=QUANTUM_DIM))
    if result.resumed:
        table.add_row("RESUMED", Text("YES", style=QUANTUM_YELLOW))

    icon = _icon()
    return Panel(
        table,
        title=f"[{QUANTUM_GREEN}]{icon} TRANSFER COMPLETE[/{QUANTUM_GREEN}]",
        border_style=QUANTUM_GREEN,
        box=box.HEAVY_EDGE,
        padding=(1, 2),
    )


# ── Error Panel ───────────────────────────────────────────────────────────


def render_error_panel(
    error: str,
    suggestion: str | None = None,
    show_trace: bool = False,
    traceback_str: str | None = None,
) -> Panel:
    """Render a structured error alert panel."""
    content = Table.grid(padding=(0, 2))
    content.add_column(style=QUANTUM_DIM, min_width=12)
    content.add_column()

    content.add_row("ERROR", Text(error, style=f"bold {QUANTUM_RED}"))
    if suggestion:
        content.add_row("FIX", Text(suggestion, style=QUANTUM_YELLOW))
    if show_trace and traceback_str:
        content.add_row("TRACE", Text(traceback_str.strip(), style=QUANTUM_DIM))

    icon = _icon()
    return Panel(
        content,
        title=f"[{QUANTUM_RED}]{icon} FLUXION ERROR[/{QUANTUM_RED}]",
        border_style=QUANTUM_RED,
        box=box.HEAVY_EDGE,
        padding=(1, 2),
    )


# ── TLS Panel ─────────────────────────────────────────────────────────────


def render_tls_panel(cert_data: dict[str, str]) -> Panel:
    """Render a TLS certificate inspection panel."""
    table = Table.grid(padding=(0, 2))
    table.add_column(style=QUANTUM_DIM, min_width=16)
    table.add_column()

    for key, value in cert_data.items():
        table.add_row(key, Text(str(value), style="white"))

    icon = _icon()
    return Panel(
        table,
        title=f"[{QUANTUM_BLUE}]{icon} TLS SECURITY[/{QUANTUM_BLUE}]",
        border_style=QUANTUM_BLUE,
        box=box.HEAVY_EDGE,
        padding=(1, 2),
    )


# ── Helpers ───────────────────────────────────────────────────────────────


def _render_bar(percent: float, layout: LayoutMode) -> str:
    """Render a text progress bar."""
    width_map = {
        LayoutMode.MINIMAL: 10,
        LayoutMode.COMPACT: 20,
        LayoutMode.STANDARD: 30,
        LayoutMode.FULL: 40,
    }
    width = width_map.get(layout, 20)
    filled = int(width * percent / 100)
    empty = width - filled
    if supports_unicode():
        return "\u2588" * filled + "\u2591" * empty
    return "#" * filled + "-" * empty


def _format_speed(bps: float) -> str:
    if bps <= 0:
        return "-- B/s"
    units = ["B/s", "KiB/s", "MiB/s", "GiB/s"]
    val = bps
    for unit in units:
        if val < 1024:
            return f"{val:.1f} {unit}"
        val /= 1024
    return f"{val:.1f} TiB/s"


def _format_bytes(b: int) -> str:
    if b <= 0:
        return "0 B"
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    val = float(b)
    for unit in units:
        if val < 1024:
            return f"{val:.1f} {unit}"
        val /= 1024
    return f"{val:.1f} PiB"


def _format_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m {secs}s"


def _phase_style(phase: str) -> str:
    styles = {
        "RESOLVING": QUANTUM_DIM,
        "CONNECTING": QUANTUM_YELLOW,
        "TLS": QUANTUM_GREEN,
        "PROTOCOL LOCK": QUANTUM_BLUE,
        "STREAM": f"bold {QUANTUM_GREEN}",
        "VERIFY": QUANTUM_YELLOW,
        "COMPLETE": f"bold {QUANTUM_GREEN}",
        "ERROR": f"bold {QUANTUM_RED}",
    }
    return styles.get(phase, "white")


# ── Help Panel ─────────────────────────────────────────────────────────────

_HELP_CATEGORIES: list[dict[str, object]] = [
    {
        "name": "TRANSPORT LAYER",
        "icon_u": "\u25b6",
        "icon_a": ">",
        "style": QUANTUM_BLUE,
        "commands": [
            ("fetch",  "Download files with adaptive multi-stream parallel transport"),
            ("stream", "Pipe URL content directly to stdout"),
            ("mirror", "Race multiple mirrors \u2014 download from the fastest endpoint"),
        ],
    },
    {
        "name": "NETWORK INTELLIGENCE",
        "icon_u": "\u25c7",
        "icon_a": "o",
        "style": QUANTUM_GREEN,
        "commands": [
            ("probe", "Deep network reconnaissance \u2014 protocol, TLS, latency, server fingerprint"),
            ("bench", "Statistical latency and throughput benchmarking with percentile analysis"),
        ],
    },
    {
        "name": "SECURITY LAYER",
        "icon_u": "\u25a3",
        "icon_a": "#",
        "style": QUANTUM_YELLOW,
        "commands": [
            ("secure", "TLS deep inspection \u2014 cert chain, ciphers, fingerprint, expiry analysis"),
        ],
    },
    {
        "name": "SYSTEM CONTROL",
        "icon_u": "\u27d0",
        "icon_a": "=",
        "style": QUANTUM_MAGENTA,
        "commands": [
            ("init",    "Initialize environment \u2014 detect OS, install deps, verify TLS"),
            ("doctor",  "Diagnose installation health and all dependency statuses"),
            ("config",  "View or modify Fluxion runtime configuration"),
            ("plugin",  "Manage protocol and command extension plugins"),
            ("version", "Display version, codename, and build information"),
            ("help",    "Display this command intelligence database"),
        ],
    },
]

_COMMAND_DETAILS: dict[str, dict[str, object]] = {
    "fetch": {
        "category": "TRANSPORT LAYER",
        "style": QUANTUM_BLUE,
        "description": (
            "Download files using adaptive multi-stream parallel transport with automatic "
            "protocol negotiation, HTTP range-request resume support, browser impersonation, "
            "and real-time Quantum HUD telemetry."
        ),
        "usage": "fluxion fetch <url> [OPTIONS]",
        "examples": [
            "fluxion fetch https://example.com/archive.tar.gz",
            "fluxion fetch https://cdn.example.com/file.zip -o ./file.zip -c 16",
            "fluxion fetch https://cdn.example.com/file.zip --sha256 e3b0c442...",
            "fluxion fetch https://protected.site/asset.bin --browser-profile chrome",
            'fluxion fetch https://api.example.com/export -H "Authorization: Bearer tok"',
        ],
        "options": [
            ("-o, --output PATH",          "Output file path (auto-derived from URL if omitted)"),
            ("-c, --connections INT",       "Max parallel connections (default: 8, max: 32)"),
            ("--no-resume",                "Disable HTTP range-request resume support"),
            ("--no-verify",                "Skip TLS certificate verification"),
            ("--timeout FLOAT",            "Request timeout in seconds (default: 30.0)"),
            ("--proxy URL",                "Proxy URL (e.g. socks5://localhost:1080)"),
            ("--sha256 HASH",              "Expected SHA-256 checksum — aborts on mismatch"),
            ("-H, --header NAME:VALUE",    "Custom header string, repeatable"),
            ("--cookie NAME=VALUE",        "Inline cookie string, repeatable"),
            ("--cookie-file PATH",         "Netscape or JSON cookie file"),
            ("--browser-cookies BROWSER",  "Import cookies: chrome / firefox / edge / safari"),
            ("--browser-profile PROFILE",  "Impersonate browser: chrome / firefox / edge / safari"),
            ("--referer URL",              "Referer URL header value"),
            ("--minimal",                  "Single-line in-place progress display"),
            ("--plain",                    "No styling — pipe-safe plain text output"),
            ("--json",                     "Machine-readable JSON result output"),
            ("--quiet",                    "Suppress all output (exit code only)"),
            ("--trace",                    "Show Python tracebacks on error"),
        ],
    },
    "stream": {
        "category": "TRANSPORT LAYER",
        "style": QUANTUM_BLUE,
        "description": (
            "Stream raw URL content directly to stdout. Optimized for piping into other tools — "
            "no intermediate files, no buffering overhead. Supports full stealth headers."
        ),
        "usage": "fluxion stream <url> [OPTIONS]",
        "examples": [
            "fluxion stream https://api.example.com/feed.json | jq '.data[]'",
            "fluxion stream https://logs.example.com/latest.log | grep ERROR",
            'fluxion stream https://api.example.com/data -H "X-API-Key: secret"',
        ],
        "options": [
            ("--no-verify",                "Skip TLS certificate verification"),
            ("-H, --header NAME:VALUE",    "Custom header string, repeatable"),
            ("--cookie NAME=VALUE",        "Inline cookie string, repeatable"),
            ("--browser-profile PROFILE",  "Browser impersonation profile"),
            ("--referer URL",              "Referer URL header value"),
            ("--trace",                    "Show Python tracebacks on error"),
        ],
    },
    "mirror": {
        "category": "TRANSPORT LAYER",
        "style": QUANTUM_BLUE,
        "description": (
            "Probe multiple mirror URLs in parallel, select the lowest-latency endpoint, "
            "and download from the optimal source. Ideal for ISO downloads and CDN selection."
        ),
        "usage": "fluxion mirror <url1> <url2> ... [OPTIONS]",
        "examples": [
            "fluxion mirror https://mirror1.example.com/file.iso https://mirror2.example.com/file.iso -o file.iso",
            "fluxion mirror https://cdn1.example.com/pkg https://cdn2.example.com/pkg",
        ],
        "options": [
            ("-o, --output PATH",  "Output file path"),
            ("--json",             "JSON output"),
            ("--quiet",            "Suppress all output"),
            ("--trace",            "Show Python tracebacks on error"),
        ],
    },
    "probe": {
        "category": "NETWORK INTELLIGENCE",
        "style": QUANTUM_GREEN,
        "description": (
            "Perform a deep network reconnaissance probe on any URL. Returns HTTP protocol version, "
            "TLS state, server fingerprint, latency measurements, range support, "
            "content type and size, and full certificate details."
        ),
        "usage": "fluxion probe <url> [OPTIONS]",
        "examples": [
            "fluxion probe https://cdn.example.com/asset.bin",
            "fluxion probe https://api.example.com --json | jq '.tls_version'",
        ],
        "options": [
            ("--no-verify",  "Skip TLS certificate verification"),
            ("--json",       "JSON output"),
            ("--quiet",      "Suppress all output"),
            ("--trace",      "Show Python tracebacks on error"),
        ],
    },
    "bench": {
        "category": "NETWORK INTELLIGENCE",
        "style": QUANTUM_GREEN,
        "description": (
            "Measure real-world network performance with full statistical analysis. "
            "Reports min/max/avg latency, P50/P95/P99 percentiles, jitter, "
            "stability score (0.0\u20131.0), and throughput in Mbps/Gbps."
        ),
        "usage": "fluxion bench <url> [OPTIONS]",
        "examples": [
            "fluxion bench https://cdn.example.com/test-payload -n 20",
            "fluxion bench https://api.example.com --json",
        ],
        "options": [
            ("-n, --iterations INT",  "Number of benchmark requests (default: 10)"),
            ("--no-verify",           "Skip TLS certificate verification"),
            ("--json",                "JSON output"),
            ("--quiet",               "Suppress all output"),
            ("--trace",               "Show Python tracebacks on error"),
        ],
    },
    "secure": {
        "category": "SECURITY LAYER",
        "style": QUANTUM_YELLOW,
        "description": (
            "Perform TLS deep inspection on any HTTPS endpoint. Extracts the full certificate "
            "chain, cipher suite, TLS version, subject and issuer details, validity window, "
            "SHA-256 fingerprint, and Subject Alternative Names (SANs)."
        ),
        "usage": "fluxion secure <url> [OPTIONS]",
        "examples": [
            "fluxion secure https://bank.example.com",
            "fluxion secure https://api.example.com --json",
        ],
        "options": [
            ("--json",   "JSON output"),
            ("--trace",  "Show Python tracebacks on error"),
        ],
    },
    "init": {
        "category": "SYSTEM CONTROL",
        "style": QUANTUM_MAGENTA,
        "description": (
            "Initialize the Fluxion environment. Detects OS and distribution, installs system "
            "dependencies (OpenSSL, build tools), creates configuration directories, "
            "and verifies the TLS certificate chain."
        ),
        "usage": "fluxion init [OPTIONS]",
        "examples": ["fluxion init"],
        "options": [
            ("--trace",  "Show Python tracebacks on error"),
        ],
    },
    "doctor": {
        "category": "SYSTEM CONTROL",
        "style": QUANTUM_MAGENTA,
        "description": (
            "Run a full diagnostic check on your Fluxion installation. Verifies Python version, "
            "platform info, OpenSSL availability, all required and optional dependencies, "
            "and configuration directory integrity."
        ),
        "usage": "fluxion doctor [OPTIONS]",
        "examples": ["fluxion doctor", "fluxion doctor --json"],
        "options": [
            ("--json",  "JSON output"),
        ],
    },
    "config": {
        "category": "SYSTEM CONTROL",
        "style": QUANTUM_MAGENTA,
        "description": (
            "View or modify Fluxion runtime configuration. Config is persisted to "
            "~/.fluxion/config.json with dynamic type coercion for booleans, integers, and strings."
        ),
        "usage": "fluxion config [OPTIONS]",
        "examples": [
            "fluxion config",
            "fluxion config --set max_connections=32",
            "fluxion config --set proxy=socks5://localhost:1080",
            "fluxion config --set enable_http3=false",
            "fluxion config --set default_browser_profile=firefox",
        ],
        "options": [
            ("--show / --no-show",   "Display current configuration (default: show)"),
            ("--set KEY=VALUE",      "Set a configuration key to a new value"),
        ],
    },
    "plugin": {
        "category": "SYSTEM CONTROL",
        "style": QUANTUM_MAGENTA,
        "description": (
            "Install, remove, and list Fluxion plugins. Plugins extend protocol support "
            "(new URL schemes) or add custom CLI commands. "
            "Package convention: fluxion-plugin-<name>."
        ),
        "usage": "fluxion plugin <action> [name] [OPTIONS]",
        "examples": [
            "fluxion plugin list",
            "fluxion plugin install s3",
            "fluxion plugin remove s3",
            "fluxion plugin list --json",
        ],
        "options": [
            ("install <name>",  "Install a plugin package"),
            ("remove <name>",   "Remove an installed plugin"),
            ("list",            "List all installed plugins"),
            ("--json",          "JSON output for list action"),
        ],
    },
    "version": {
        "category": "SYSTEM CONTROL",
        "style": QUANTUM_MAGENTA,
        "description": "Display Fluxion version number, codename, and system build information.",
        "usage": "fluxion version",
        "examples": ["fluxion version"],
        "options": [],
    },
    "help": {
        "category": "SYSTEM CONTROL",
        "style": QUANTUM_MAGENTA,
        "description": (
            "Display the command intelligence database. Pass a command name for detailed "
            "reference documentation including all options and usage examples."
        ),
        "usage": "fluxion help [command]",
        "examples": [
            "fluxion help",
            "fluxion help fetch",
            "fluxion help probe",
        ],
        "options": [],
    },
}


def _help_header(subtitle: str, uni: bool) -> Text:
    """Render an advanced sci-fi header for the help command."""
    layout = detect_layout()
    width = get_terminal_width()
    inner = max(width - 4, 40)

    if layout == LayoutMode.MINIMAL:
        t = Text()
        t.append("\u26a1 FLUXION  " if uni else "* FLUXION  ", style=f"bold {QUANTUM_BLUE}")
        t.append(subtitle, style=QUANTUM_DIM)
        return t

    if layout == LayoutMode.COMPACT:
        t = Text()
        t.append(f"  {_icon()}  ", style=QUANTUM_BLUE)
        t.append("FLUXION", style=f"bold {QUANTUM_BLUE}")
        t.append(f"  v{__version__}", style=QUANTUM_DIM)
        t.append(f"  \u2500  {subtitle}", style=f"dim {QUANTUM_BLUE}")
        return t

    if layout == LayoutMode.STANDARD:
        t = Text()
        t.append(f"  {_icon()}  ", style=QUANTUM_BLUE)
        t.append("FLUXION", style=f"bold {QUANTUM_BLUE}")
        t.append(f"  v{__version__} [{__codename__}]", style=QUANTUM_DIM)
        t.append(f"  \u2500\u2500  {subtitle}", style=f"dim {QUANTUM_BLUE}")
        return t

    # FULL layout \u2014 5-line sci-fi box with integrated status bar
    icon = _icon()
    title_str = f"  {icon}  FLUXION  \u2550\u2550  {subtitle}"
    sub_str = f"  Intelligent Network Command Engine  \u25c6  v{__version__} [{__codename__}]"
    stat_str = (
        f"  UPLINK: NOMINAL  \u25c6  PROTOCOLS: HTTP/1.1 \u00b7 HTTP/2 \u00b7 HTTP/3"
        f" \u00b7 FTP \u00b7 SFTP  \u25c6  COMMANDS: 12  \u25c6  ENGINE: ONLINE"
    )
    t = Text()
    if uni:
        bar = "\u2550" * inner
        t.append(f"\u2554{bar}\u2557\n", style=QUANTUM_BLUE)
        t.append("\u2551", style=QUANTUM_BLUE)
        t.append(title_str.ljust(inner), style=f"bold {QUANTUM_BLUE}")
        t.append("\u2551\n", style=QUANTUM_BLUE)
        t.append("\u2551", style=QUANTUM_BLUE)
        t.append(sub_str.ljust(inner), style=QUANTUM_DIM)
        t.append("\u2551\n", style=QUANTUM_BLUE)
        t.append(f"\u2560{bar}\u2563\n", style=f"dim {QUANTUM_BLUE}")
        t.append("\u2551", style=QUANTUM_BLUE)
        t.append(stat_str.ljust(inner), style=f"dim {QUANTUM_GREEN}")
        t.append("\u2551\n", style=QUANTUM_BLUE)
        t.append(f"\u255a{bar}\u255d", style=QUANTUM_BLUE)
    else:
        bar = "=" * inner
        t.append(f"+{bar}+\n", style=QUANTUM_BLUE)
        t.append("|", style=QUANTUM_BLUE)
        t.append(title_str.ljust(inner), style=f"bold {QUANTUM_BLUE}")
        t.append("|\n", style=QUANTUM_BLUE)
        t.append("|", style=QUANTUM_BLUE)
        t.append(sub_str.ljust(inner), style=QUANTUM_DIM)
        t.append("|\n", style=QUANTUM_BLUE)
        t.append(f"|{bar}|\n", style=f"dim {QUANTUM_BLUE}")
        t.append("|", style=QUANTUM_BLUE)
        t.append(stat_str.ljust(inner), style=f"dim {QUANTUM_GREEN}")
        t.append("|\n", style=QUANTUM_BLUE)
        t.append(f"+{bar}+", style=QUANTUM_BLUE)
    return t


def _system_matrix_panel(uni: bool) -> Panel:
    """Render a compact system intelligence matrix panel."""
    pulse = "\u25cf" if uni else "*"
    table = Table.grid(padding=(0, 2))
    table.add_column(style=QUANTUM_DIM, min_width=11)
    table.add_column(style=f"bold {QUANTUM_BLUE}", min_width=12)
    table.add_column(style=QUANTUM_DIM, min_width=11)
    table.add_column(style=f"bold {QUANTUM_GREEN}", min_width=14)
    table.add_column(style=QUANTUM_DIM, min_width=11)
    table.add_column(style=f"bold {QUANTUM_MAGENTA}", min_width=10)
    table.add_row(
        "VERSION",  f"{__version__}",
        "CODENAME", f"{__codename__}",
        "COMMANDS", "12",
    )
    table.add_row(
        "ENGINE",  f"{pulse} ONLINE",
        "TLS",     f"{pulse} VERIFIED",
        "STREAMS", f"{pulse} NOMINAL",
    )
    icon = _icon()
    return Panel(
        table,
        title=f"[{QUANTUM_BLUE}]{icon}  INTELLIGENCE MATRIX[/{QUANTUM_BLUE}]",
        border_style=f"dim {QUANTUM_BLUE}",
        box=box.HEAVY_EDGE,
        padding=(0, 2),
        title_align="left",
    )


def _field_ops_panel(uni: bool) -> Panel:
    """Render a panel of common field operation patterns."""
    arrow = "\u27a4" if uni else ">"
    ops_table = Table.grid(padding=(0, 2))
    ops_table.add_column(style=QUANTUM_DIM, min_width=3)
    ops_table.add_column(style=f"bold {QUANTUM_GREEN}")
    ops_table.add_column(style=QUANTUM_DIM)
    ops = [
        (
            "fluxion fetch <url> -c 16 --sha256 <hash>",
            "Parallel download with integrity verification",
        ),
        (
            "fluxion fetch <url> --browser-profile chrome --browser-cookies firefox",
            "Stealth mode with live browser cookies",
        ),
        (
            "fluxion probe <url> && fluxion bench <url> -n 20",
            "Network recon + statistical performance analysis",
        ),
        (
            "fluxion mirror <url1> <url2> <url3> -o output.iso",
            "Auto-select fastest mirror endpoint",
        ),
        (
            "fluxion stream <url> | jq '.data[]'",
            "Pipe-safe streaming to stdout",
        ),
        (
            "fluxion secure <url> --json | jq '.fingerprint_sha256'",
            "Extract TLS fingerprint via JSON pipeline",
        ),
    ]
    for cmd, desc in ops:
        ops_table.add_row(arrow, cmd, desc)
    play_ic = "\u25b6" if uni else ">"
    return Panel(
        ops_table,
        title=f"[{QUANTUM_GREEN}]{play_ic}  FIELD OPERATIONS[/{QUANTUM_GREEN}]",
        border_style=QUANTUM_GREEN,
        box=box.HEAVY_EDGE,
        padding=(1, 2),
        title_align="left",
    )


def _sci_fi_footer(uni: bool) -> Text:
    """Render a multi-indicator Quantum status footer."""
    sep = " \u25c6 " if uni else " * "
    width = get_terminal_width()
    bar_char = "\u2500" if uni else "-"
    bar = bar_char * max(width - 4, 40)
    bolt = "\u26a1 " if uni else ""
    t = Text()
    t.append("\n", style="")
    t.append(f"  {bar}\n", style=f"dim {QUANTUM_BLUE}")
    indicators = [
        f"{bolt}QUANTUM ENGINE ONLINE",
        "PROTOCOLS NOMINAL",
        "TLS VERIFIED",
        "STREAMS READY",
    ]
    t.append(f"  {sep.join(indicators)}\n", style=f"dim {QUANTUM_BLUE}")
    hint_sep = "  \u00b7  " if uni else "  |  "
    hints = [
        "fluxion help <command>",
        "fluxion <command> --help",
        "github.com/scorpiocodex/Fluxion",
    ]
    t.append(f"  {hint_sep.join(hints)}\n", style=QUANTUM_DIM)
    return t


def render_help_panel(command_name: str | None = None) -> Group:
    """Render the sci-fi Quantum Command Intelligence Database."""
    uni = supports_unicode()

    if command_name:
        return _render_command_detail(command_name.lower(), uni)
    return _render_help_overview(uni)


def _render_help_overview(uni: bool) -> Group:
    """Render the full command intelligence database overview."""
    layout = detect_layout()
    parts: list[object] = [
        _help_header("QUANTUM COMMAND INTELLIGENCE DATABASE", uni),
        Text(""),
    ]

    # System intelligence matrix \u2014 STANDARD and FULL modes only
    if layout in (LayoutMode.STANDARD, LayoutMode.FULL):
        parts.append(_system_matrix_panel(uni))
        parts.append(Text(""))

    # Command categories
    for cat in _HELP_CATEGORIES:
        cat_icon = cat["icon_u"] if uni else cat["icon_a"]
        style = str(cat["style"])
        name = str(cat["name"])
        cmds: list[tuple[str, str]] = cat["commands"]  # type: ignore[assignment]

        cmd_table = Table.grid(padding=(0, 3))
        cmd_table.add_column(min_width=10, style=f"bold {style}")
        cmd_table.add_column(style="white")
        for cmd_name, cmd_desc in cmds:
            cmd_table.add_row(cmd_name, cmd_desc)

        parts.append(
            Panel(
                cmd_table,
                title=f"[{style}]{cat_icon}  {name}[/{style}]",
                border_style=style,
                box=box.HEAVY_EDGE,
                padding=(1, 2),
                title_align="left",
            )
        )

    # Field operations \u2014 STANDARD and FULL modes only
    if layout in (LayoutMode.STANDARD, LayoutMode.FULL):
        parts.append(Text(""))
        parts.append(_field_ops_panel(uni))

    # Usage hints
    hint_ic = "\u27a4" if uni else ">"
    opt_ic = "\u27d0" if uni else "="
    usage_table = Table.grid(padding=(0, 2))
    usage_table.add_column(style=QUANTUM_DIM, min_width=3)
    usage_table.add_column(style=f"bold {QUANTUM_BLUE}", min_width=38)
    usage_table.add_column(style=QUANTUM_DIM)
    usage_table.add_row(hint_ic, "fluxion <command> --help", "Native flag-level help for any command")
    usage_table.add_row(hint_ic, "fluxion help <command>",   "Full reference with options and examples")

    parts.append(Text(""))
    parts.append(
        Panel(
            usage_table,
            title=f"[{QUANTUM_DIM}]{opt_ic}  USAGE[/{QUANTUM_DIM}]",
            border_style="dim",
            box=box.HEAVY_EDGE,
            padding=(1, 2),
            title_align="left",
        )
    )
    parts.append(_sci_fi_footer(uni))
    return Group(*parts)


def _render_command_detail(command_name: str, uni: bool) -> Group:
    """Render detailed sci-fi help for a specific command."""
    icon = _icon()
    details = _COMMAND_DETAILS.get(command_name)
    parts: list[object] = []

    if not details:
        parts.append(_help_header("COMMAND INTELLIGENCE DATABASE", uni))
        parts.append(Text(""))
        err = Text()
        err.append(f"  {icon} ", style=QUANTUM_RED)
        err.append("Unknown command: ", style=f"bold {QUANTUM_RED}")
        err.append(command_name, style=QUANTUM_WHITE)
        parts.append(err)
        parts.append(Text(""))
        hint = Text()
        hint.append("  Run ", style=QUANTUM_DIM)
        hint.append("fluxion help", style=f"bold {QUANTUM_BLUE}")
        hint.append(" to see all available commands.", style=QUANTUM_DIM)
        parts.append(hint)
        parts.append(_sci_fi_footer(uni))
        return Group(*parts)

    style = str(details["style"])
    category = str(details["category"])
    description = str(details["description"])
    usage = str(details["usage"])
    examples: list[str] = details["examples"]  # type: ignore[assignment]
    options: list[tuple[str, str]] = details["options"]  # type: ignore[assignment]

    # Find category icon and gather related commands from the same category
    cat_icon = ">" if not uni else "\u25b6"
    related_cmds: list[str] = []
    for cat in _HELP_CATEGORIES:
        if cat["name"] == category:
            cat_icon = str(cat["icon_u"]) if uni else str(cat["icon_a"])
            related_cmds = [
                cmd_name
                for cmd_name, _ in cat["commands"]  # type: ignore[misc]
                if cmd_name != command_name
            ]
            break

    sep = "\u2500" if uni else "--"
    parts.append(_help_header(f"COMMAND REFERENCE  {sep}  {command_name.upper()}", uni))
    parts.append(Text(""))

    # Overview panel
    ov = Table.grid(padding=(0, 2))
    ov.add_column(style=QUANTUM_DIM, min_width=16)
    ov.add_column(style="white")
    ov.add_row("COMMAND",     Text(command_name, style=f"bold {style}"))
    ov.add_row("CATEGORY",    Text(f"{cat_icon}  {category}", style=style))
    ov.add_row("DESCRIPTION", Text(description, style="white"))
    ov.add_row("SYNTAX",      Text(usage, style=f"bold {QUANTUM_BLUE}"))
    if related_cmds:
        ov.add_row("SEE ALSO",    Text("  ".join(related_cmds), style=f"dim {style}"))
    parts.append(
        Panel(
            ov,
            title=f"[{style}]{cat_icon}  OVERVIEW[/{style}]",
            border_style=style,
            box=box.HEAVY_EDGE,
            padding=(1, 2),
            title_align="left",
        )
    )

    # Options panel
    if options:
        opt_ic = "\u27d0" if uni else "="
        opt = Table.grid(padding=(0, 2))
        opt.add_column(style=f"bold {QUANTUM_BLUE}", min_width=30)
        opt.add_column(style="white")
        for flag, desc in options:
            opt.add_row(flag, desc)
        parts.append(
            Panel(
                opt,
                title=f"[{QUANTUM_DIM}]{opt_ic}  OPTIONS[/{QUANTUM_DIM}]",
                border_style="dim",
                box=box.HEAVY_EDGE,
                padding=(1, 2),
                title_align="left",
            )
        )

    # Examples panel
    if examples:
        ex_ic = "\u27a4" if uni else "$"
        ex_table = Table.grid(padding=(0, 1))
        ex_table.add_column()
        for ex in examples:
            row = Text()
            row.append(f"  {ex_ic}  ", style=QUANTUM_DIM)
            row.append(ex, style=f"bold {QUANTUM_GREEN}")
            ex_table.add_row(row)
        play_ic = "\u25b6" if uni else ">"
        parts.append(
            Panel(
                ex_table,
                title=f"[{QUANTUM_GREEN}]{play_ic}  EXAMPLES[/{QUANTUM_GREEN}]",
                border_style=QUANTUM_GREEN,
                box=box.HEAVY_EDGE,
                padding=(1, 2),
                title_align="left",
            )
        )

    parts.append(_sci_fi_footer(uni))
    return Group(*parts)
