"""HUD renderer — manages live display updates with in-place refresh."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.live import Live

from fluxion.hud.layout import LayoutMode, detect_layout, register_resize_handler
from fluxion.hud.panels import (
    render_bench_panel,
    render_error_panel,
    render_header,
    render_probe_panel,
    render_progress_panel,
    render_result_panel,
)
from fluxion.models import BenchResult, FetchResult, OutputMode, ProbeResult, TransferStats


class HUDRenderer:
    """Manages the Quantum Command HUD lifecycle.

    Handles in-place updates, terminal resize, and output mode switching.
    """

    def __init__(
        self,
        console: Console | None = None,
        output_mode: OutputMode = OutputMode.DEFAULT,
        refresh_rate: float = 3.3,
    ) -> None:
        self._console = console or Console()
        self._output_mode = output_mode
        self._refresh_rate = refresh_rate
        self._layout = detect_layout()
        self._live: Live | None = None

        register_resize_handler(self._on_resize)

    @property
    def console(self) -> Console:
        return self._console

    @property
    def output_mode(self) -> OutputMode:
        return self._output_mode

    @property
    def layout(self) -> LayoutMode:
        return self._layout

    def _on_resize(self) -> None:
        self._layout = detect_layout()

    # ── Header ───────────────────────────────────────────────────────

    def print_header(self) -> None:
        """Print the Fluxion branded header."""
        if self._output_mode in (OutputMode.JSON, OutputMode.QUIET, OutputMode.PLAIN):
            return
        header = render_header(self._console)
        self._console.print(header)

    # ── Live transfer display ────────────────────────────────────────

    def start_live(self) -> None:
        """Begin a live-updating HUD session."""
        if self._output_mode != OutputMode.DEFAULT:
            return
        self._live = Live(
            console=self._console,
            refresh_per_second=self._refresh_rate,
            transient=True,
        )
        self._live.start()

    def update_transfer(self, stats: TransferStats, url: str = "") -> None:
        """Update the transfer HUD panel in-place."""
        if self._output_mode == OutputMode.JSON:
            return
        if self._output_mode == OutputMode.QUIET:
            return

        if self._output_mode == OutputMode.MINIMAL:
            pct = 0.0
            if stats.bytes_total and stats.bytes_total > 0:
                pct = (stats.bytes_downloaded / stats.bytes_total) * 100
            from fluxion.hud.panels import _format_speed

            speed = _format_speed(stats.speed_bytes_per_sec)
            self._console.print(
                f"\r{stats.phase.value} {pct:.1f}% {speed}",
                end="",
                highlight=False,
            )
            return

        if self._output_mode == OutputMode.PLAIN:
            if stats.bytes_total and stats.bytes_total > 0:
                pct = (stats.bytes_downloaded / stats.bytes_total) * 100
                self._console.print(f"{stats.phase.value}: {pct:.1f}%", highlight=False)
            return

        # Default: full HUD
        panel = render_progress_panel(stats, url)
        if self._live:
            self._live.update(panel)
        else:
            self._console.print(panel)

    def stop_live(self) -> None:
        """Stop the live HUD session."""
        if self._live:
            self._live.stop()
            self._live = None

    # ── Static panels ────────────────────────────────────────────────

    def print_probe(self, result: ProbeResult) -> None:
        """Print the probe panel."""
        if self._output_mode == OutputMode.JSON:
            self._console.print_json(result.model_dump_json())
            return
        if self._output_mode == OutputMode.QUIET:
            self._console.print(result.url)
            return
        panel = render_probe_panel(result)
        self._console.print(panel)

    def print_bench(self, result: BenchResult) -> None:
        """Print the benchmark panel."""
        if self._output_mode == OutputMode.JSON:
            self._console.print_json(result.model_dump_json())
            return
        if self._output_mode == OutputMode.QUIET:
            self._console.print(f"{result.latency_avg_ms:.2f}ms avg")
            return
        panel = render_bench_panel(result)
        self._console.print(panel)

    def print_error(
        self,
        error: str,
        suggestion: str | None = None,
        show_trace: bool = False,
        traceback_str: str | None = None,
    ) -> None:
        """Print a structured error panel."""
        if self._output_mode == OutputMode.JSON:
            import json

            self._console.print_json(
                json.dumps({"error": error, "suggestion": suggestion})
            )
            return
        if self._output_mode == OutputMode.QUIET:
            self._console.print(f"ERROR: {error}")
            return
        panel = render_error_panel(error, suggestion, show_trace, traceback_str)
        self._console.print(panel)

    def print_result(self, data: Any) -> None:
        """Print a fetch result or generic data with structured formatting."""
        if self._output_mode == OutputMode.JSON:
            if hasattr(data, "model_dump_json"):
                self._console.print_json(data.model_dump_json())
            else:
                import json

                self._console.print_json(json.dumps(data, default=str))
            return

        # Use structured result panel for FetchResult
        if isinstance(data, FetchResult):
            panel = render_result_panel(data)
            self._console.print(panel)
            return

        if hasattr(data, "model_dump"):
            from rich.table import Table

            table = Table.grid(padding=(0, 2))
            table.add_column(style="dim", min_width=14)
            table.add_column()
            for key, value in data.model_dump().items():
                table.add_row(key.upper(), str(value))
            self._console.print(table)
        else:
            self._console.print(data)
