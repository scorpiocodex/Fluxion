"""Tests for HUD rendering."""

import io
import os

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from fluxion.hud.layout import LayoutMode, detect_layout, get_terminal_width, supports_unicode
from fluxion.hud.panels import (
    _format_bytes,
    _format_speed,
    _format_time,
    _phase_style,
    _render_bar,
    render_bench_panel,
    render_error_panel,
    render_header,
    render_probe_panel,
    render_progress_panel,
    render_result_panel,
    render_tls_panel,
    _icon,
    _flux_icon,
    _phase_icon,
)
from fluxion.hud.renderer import HUDRenderer
from fluxion.models import (
    BenchResult,
    FetchResult,
    FluxMode,
    OutputMode,
    ProbeResult,
    Protocol,
    TransferPhase,
    TransferStats,
)
from pathlib import Path


class TestLayout:
    def test_detect_minimal(self) -> None:
        assert detect_layout(50) == LayoutMode.MINIMAL

    def test_detect_compact(self) -> None:
        assert detect_layout(75) == LayoutMode.COMPACT

    def test_detect_standard(self) -> None:
        assert detect_layout(100) == LayoutMode.STANDARD

    def test_detect_full(self) -> None:
        assert detect_layout(150) == LayoutMode.FULL

    def test_detect_boundary_60(self) -> None:
        assert detect_layout(59) == LayoutMode.MINIMAL
        assert detect_layout(60) == LayoutMode.COMPACT

    def test_detect_boundary_90(self) -> None:
        assert detect_layout(89) == LayoutMode.COMPACT
        assert detect_layout(90) == LayoutMode.STANDARD

    def test_detect_boundary_130(self) -> None:
        assert detect_layout(129) == LayoutMode.STANDARD
        assert detect_layout(130) == LayoutMode.FULL

    def test_get_terminal_width(self) -> None:
        w = get_terminal_width()
        assert isinstance(w, int)
        assert w > 0

    def test_supports_unicode(self) -> None:
        result = supports_unicode()
        assert isinstance(result, bool)


class TestFormatHelpers:
    def test_format_bytes_zero(self) -> None:
        assert _format_bytes(0) == "0 B"

    def test_format_bytes_negative(self) -> None:
        assert _format_bytes(-1) == "0 B"

    def test_format_bytes_kib(self) -> None:
        assert "KiB" in _format_bytes(2048)

    def test_format_bytes_mib(self) -> None:
        assert "MiB" in _format_bytes(5 * 1024 * 1024)

    def test_format_bytes_gib(self) -> None:
        assert "GiB" in _format_bytes(2 * 1024 * 1024 * 1024)

    def test_format_speed_zero(self) -> None:
        assert "B/s" in _format_speed(0)

    def test_format_speed_kib(self) -> None:
        assert "KiB/s" in _format_speed(2048)

    def test_format_speed_mib(self) -> None:
        assert "MiB/s" in _format_speed(10 * 1024 * 1024)

    def test_format_time_seconds(self) -> None:
        assert _format_time(30) == "30s"

    def test_format_time_minutes(self) -> None:
        result = _format_time(90)
        assert "m" in result

    def test_format_time_hours(self) -> None:
        result = _format_time(7200)
        assert "h" in result

    def test_render_bar_unicode(self) -> None:
        bar = _render_bar(50.0, LayoutMode.STANDARD)
        assert len(bar) == 30  # STANDARD width

    def test_render_bar_full(self) -> None:
        bar = _render_bar(100.0, LayoutMode.COMPACT)
        assert len(bar) == 20  # COMPACT width

    def test_render_bar_zero(self) -> None:
        bar = _render_bar(0.0, LayoutMode.MINIMAL)
        assert len(bar) == 10  # MINIMAL width


class TestIcons:
    def test_icon_returns_string(self) -> None:
        icon = _icon()
        assert isinstance(icon, str)
        assert len(icon) >= 1

    def test_flux_icon_returns_string(self) -> None:
        icon = _flux_icon()
        assert isinstance(icon, str)
        assert len(icon) >= 1

    def test_phase_icon_known(self) -> None:
        icon = _phase_icon("STREAM")
        assert isinstance(icon, str)

    def test_phase_icon_unknown(self) -> None:
        icon = _phase_icon("UNKNOWN_PHASE")
        assert icon == "."

    def test_phase_style_known(self) -> None:
        style = _phase_style("COMPLETE")
        assert "green" in style

    def test_phase_style_unknown(self) -> None:
        style = _phase_style("UNKNOWN")
        assert style == "white"


class TestPanels:
    def test_render_header_full(self) -> None:
        result = render_header()
        assert result is not None

    def test_render_progress_panel(self) -> None:
        stats = TransferStats(
            bytes_downloaded=512,
            bytes_total=1024,
            speed_bytes_per_sec=256.0,
            phase=TransferPhase.STREAM,
            flux_mode=FluxMode.PARALLEL,
            active_connections=4,
            eta_seconds=2.0,
        )
        panel = render_progress_panel(stats, url="https://example.com/file")
        assert isinstance(panel, Panel)

    def test_render_progress_panel_no_total(self) -> None:
        stats = TransferStats(
            bytes_downloaded=512,
            speed_bytes_per_sec=100.0,
            phase=TransferPhase.STREAM,
        )
        panel = render_progress_panel(stats)
        assert isinstance(panel, Panel)

    def test_render_probe_panel(self) -> None:
        result = ProbeResult(
            url="https://example.com",
            http_version="HTTP/2",
            latency_ms=42.0,
            server="nginx",
            supports_range=True,
            tls_version="TLSv1.3",
            content_length=1024,
        )
        panel = render_probe_panel(result)
        assert isinstance(panel, Panel)

    def test_render_bench_panel(self) -> None:
        result = BenchResult(
            url="https://example.com",
            latency_avg_ms=50.0,
            stability_score=0.92,
            requests_completed=10,
        )
        panel = render_bench_panel(result)
        assert isinstance(panel, Panel)

    def test_render_bench_panel_poor_stability(self) -> None:
        result = BenchResult(
            url="https://example.com",
            latency_avg_ms=200.0,
            stability_score=0.3,
            requests_completed=5,
            requests_failed=5,
        )
        panel = render_bench_panel(result)
        assert isinstance(panel, Panel)

    def test_render_error_panel(self) -> None:
        panel = render_error_panel(
            "Connection refused",
            suggestion="Check the URL",
        )
        assert isinstance(panel, Panel)

    def test_render_error_panel_with_trace(self) -> None:
        panel = render_error_panel(
            "Timeout",
            suggestion="Increase timeout",
            show_trace=True,
            traceback_str="Traceback ...",
        )
        assert isinstance(panel, Panel)

    def test_render_error_panel_no_suggestion(self) -> None:
        panel = render_error_panel("Unknown error")
        assert isinstance(panel, Panel)

    def test_render_result_panel(self) -> None:
        result = FetchResult(
            url="https://example.com/file.bin",
            output_path=Path("file.bin"),
            bytes_downloaded=1024,
            elapsed_seconds=1.5,
            speed_bytes_per_sec=682.0,
            protocol_used=Protocol.HTTP2,
            sha256="abcdef1234567890",
            resumed=True,
        )
        panel = render_result_panel(result)
        assert isinstance(panel, Panel)

    def test_render_tls_panel(self) -> None:
        cert_data = {
            "SUBJECT CN": "example.com",
            "ISSUER": "Let's Encrypt",
            "TLS VERSION": "TLSv1.3",
        }
        panel = render_tls_panel(cert_data)
        assert isinstance(panel, Panel)


class TestHUDRenderer:
    def test_creation(self) -> None:
        renderer = HUDRenderer(output_mode=OutputMode.DEFAULT)
        assert renderer.output_mode == OutputMode.DEFAULT

    def test_json_mode(self) -> None:
        devnull = open(os.devnull, "w")
        try:
            console = Console(file=devnull, force_terminal=False)
            renderer = HUDRenderer(console=console, output_mode=OutputMode.JSON)
            renderer.print_header()  # No-op in JSON mode
        finally:
            devnull.close()

    def test_quiet_mode_header(self) -> None:
        buf = io.StringIO()
        console = Console(file=buf, force_terminal=False)
        renderer = HUDRenderer(console=console, output_mode=OutputMode.QUIET)
        renderer.print_header()  # No-op in QUIET mode
        assert buf.getvalue() == ""

    def test_plain_mode_header(self) -> None:
        buf = io.StringIO()
        console = Console(file=buf, force_terminal=False)
        renderer = HUDRenderer(console=console, output_mode=OutputMode.PLAIN)
        renderer.print_header()  # No-op in PLAIN mode
        assert buf.getvalue() == ""

    def test_layout_property(self) -> None:
        renderer = HUDRenderer()
        assert isinstance(renderer.layout, LayoutMode)

    def test_print_probe_json(self) -> None:
        buf = io.StringIO()
        console = Console(file=buf, force_terminal=False)
        renderer = HUDRenderer(console=console, output_mode=OutputMode.JSON)
        result = ProbeResult(url="https://example.com")
        renderer.print_probe(result)
        assert "example.com" in buf.getvalue()

    def test_print_bench_quiet(self) -> None:
        buf = io.StringIO()
        console = Console(file=buf, force_terminal=False)
        renderer = HUDRenderer(console=console, output_mode=OutputMode.QUIET)
        result = BenchResult(url="https://example.com", latency_avg_ms=42.5)
        renderer.print_bench(result)
        assert "42.50" in buf.getvalue()

    def test_print_error_json(self) -> None:
        buf = io.StringIO()
        console = Console(file=buf, force_terminal=False)
        renderer = HUDRenderer(console=console, output_mode=OutputMode.JSON)
        renderer.print_error("test error", suggestion="fix it")
        output = buf.getvalue()
        assert "test error" in output

    def test_print_error_quiet(self) -> None:
        buf = io.StringIO()
        console = Console(file=buf, force_terminal=False)
        renderer = HUDRenderer(console=console, output_mode=OutputMode.QUIET)
        renderer.print_error("test error")
        assert "ERROR" in buf.getvalue()

    def test_print_result_fetch(self) -> None:
        buf = io.StringIO()
        console = Console(file=buf, force_terminal=False)
        renderer = HUDRenderer(console=console, output_mode=OutputMode.DEFAULT)
        result = FetchResult(
            url="https://example.com/file.bin",
            output_path=Path("file.bin"),
            bytes_downloaded=1024,
            elapsed_seconds=1.0,
            speed_bytes_per_sec=1024.0,
            protocol_used=Protocol.HTTP2,
        )
        renderer.print_result(result)
        assert "file.bin" in buf.getvalue()

    def test_print_result_json(self) -> None:
        buf = io.StringIO()
        console = Console(file=buf, force_terminal=False)
        renderer = HUDRenderer(console=console, output_mode=OutputMode.JSON)
        result = FetchResult(
            url="https://example.com/file.bin",
            output_path=Path("file.bin"),
            bytes_downloaded=1024,
            elapsed_seconds=1.0,
            speed_bytes_per_sec=1024.0,
            protocol_used=Protocol.HTTP2,
        )
        renderer.print_result(result)
        assert "file.bin" in buf.getvalue()

    def test_start_stop_live_non_default(self) -> None:
        renderer = HUDRenderer(output_mode=OutputMode.JSON)
        renderer.start_live()  # No-op
        renderer.stop_live()  # No-op

    def test_update_transfer_json_noop(self) -> None:
        renderer = HUDRenderer(output_mode=OutputMode.JSON)
        stats = TransferStats()
        renderer.update_transfer(stats)  # No-op

    def test_update_transfer_quiet_noop(self) -> None:
        renderer = HUDRenderer(output_mode=OutputMode.QUIET)
        stats = TransferStats()
        renderer.update_transfer(stats)  # No-op
