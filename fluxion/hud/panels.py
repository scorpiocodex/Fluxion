"""HUD panel rendering — header, progress, probe, bench, error, result panels."""

from __future__ import annotations

from rich.console import Console, Group
from rich.panel import Panel
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

    title = f"  {icon}  FLUXION"
    subtitle = f"Intelligent Network Command Engine  v{__version__} [{__codename__}]"

    header_text = Text()
    if uni:
        bar = "\u2550" * inner
        header_text.append(f"\u2554{bar}\u2557\n", style=QUANTUM_BLUE)
        header_text.append("\u2551", style=QUANTUM_BLUE)
        header_text.append(title.ljust(inner), style=f"bold {QUANTUM_BLUE}")
        header_text.append("\u2551\n", style=QUANTUM_BLUE)
        header_text.append("\u2551", style=QUANTUM_BLUE)
        header_text.append(f"  {subtitle}".ljust(inner), style=QUANTUM_DIM)
        header_text.append("\u2551\n", style=QUANTUM_BLUE)
        header_text.append(f"\u255a{bar}\u255d", style=QUANTUM_BLUE)
    else:
        bar = "=" * inner
        header_text.append(f"+{bar}+\n", style=QUANTUM_BLUE)
        header_text.append("|", style=QUANTUM_BLUE)
        header_text.append(title.ljust(inner), style=f"bold {QUANTUM_BLUE}")
        header_text.append("|\n", style=QUANTUM_BLUE)
        header_text.append("|", style=QUANTUM_BLUE)
        header_text.append(f"  {subtitle}".ljust(inner), style=QUANTUM_DIM)
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
