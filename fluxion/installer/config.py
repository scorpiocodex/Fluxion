"""Configuration management — view/edit Fluxion settings."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from fluxion.hud.panels import QUANTUM_BLUE, _icon
from fluxion.models import FluxionConfig

CONFIG_PATH = Path.home() / ".fluxion" / "config.json"


def load_config() -> FluxionConfig:
    """Load configuration from disk, or return defaults."""
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return FluxionConfig.model_validate(data)
        except json.JSONDecodeError:
            pass
        except Exception:
            pass
    return FluxionConfig()


def save_config(config: FluxionConfig) -> None:
    """Persist configuration to disk."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        config.model_dump_json(indent=2),
        encoding="utf-8",
    )


def show_config(console: Console) -> None:
    """Print current configuration."""
    config = load_config()
    icon = _icon()

    table = Table.grid(padding=(0, 2))
    table.add_column(style="dim", min_width=20)
    table.add_column()

    for key, value in config.model_dump().items():
        table.add_row(key.upper(), str(value))

    panel = Panel(
        table,
        title=f"[{QUANTUM_BLUE}]{icon} CONFIGURATION[/{QUANTUM_BLUE}]",
        border_style=QUANTUM_BLUE,
        padding=(1, 2),
    )
    console.print(panel)
    console.print(f"  Config file: {CONFIG_PATH}\n")
