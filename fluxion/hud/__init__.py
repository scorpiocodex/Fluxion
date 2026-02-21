"""Quantum Command HUD — Sci-Fi CLI rendering engine."""

from fluxion.hud.renderer import HUDRenderer
from fluxion.hud.layout import LayoutMode, detect_layout
from fluxion.hud.panels import (
    render_header,
    render_progress_panel,
    render_probe_panel,
    render_bench_panel,
    render_error_panel,
)

__all__ = [
    "HUDRenderer",
    "LayoutMode",
    "detect_layout",
    "render_header",
    "render_progress_panel",
    "render_probe_panel",
    "render_bench_panel",
    "render_error_panel",
]
