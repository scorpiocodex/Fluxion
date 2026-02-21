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


LOCAL_CONFIG_PATH = Path("./fluxion.json")

def load_config() -> FluxionConfig:
    import os
    from typing import Any
    from fluxion.exceptions import FluxionError
    
    data: dict[str, Any] = {}
    
    # 1. Global config file
    if CONFIG_PATH.exists():
        try:
            global_data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            data.update(global_data)
        except json.JSONDecodeError as exc:
            raise FluxionError(
                f"Configuration file {CONFIG_PATH} is corrupted: {exc}",
                suggestion="Fix the JSON syntax or remove the file to reset.",
            ) from exc
        except OSError as exc:
            raise FluxionError(f"Cannot read config file: {exc}") from exc
            
    # 2. Local config file override
    if LOCAL_CONFIG_PATH.exists():
        try:
            local_data = json.loads(LOCAL_CONFIG_PATH.read_text(encoding="utf-8"))
            data.update(local_data)
        except json.JSONDecodeError as exc:
            raise FluxionError(
                f"Local configuration file {LOCAL_CONFIG_PATH} is corrupted: {exc}",
            ) from exc
        except OSError as exc:
            import logging
            logging.getLogger("fluxion.config").debug(f"No local fluxion.json configuration override discovered: {exc}")

    # 3. Environment variables override
    for key, value in os.environ.items():
        if not isinstance(key, str) or not isinstance(value, str):
            continue
        if key.upper().startswith("FLUXION_"):
            field = key[8:].lower()
            if field in FluxionConfig.model_fields:
                field_type = FluxionConfig.model_fields[field].annotation
                try:
                    if field_type is bool:
                        data[field] = value.lower() in ("true", "1", "yes")
                    elif field_type is int:
                        data[field] = int(value)
                    elif field_type is float:
                        data[field] = float(value)
                    else:
                        data[field] = value
                except ValueError as exc:
                    import logging
                    logging.getLogger("fluxion.config").warning(f"Failed to parse environment config FLUXION_{field.upper()}: {exc}")

    return FluxionConfig.model_validate(data)


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

    from rich import box
    panel = Panel(
        table,
        title=f"[{QUANTUM_BLUE}]{icon} CONFIGURATION[/{QUANTUM_BLUE}]",
        border_style=QUANTUM_BLUE,
        box=box.HEAVY_EDGE,
        padding=(1, 2),
    )
    console.print(panel)
    console.print(f"  Config file: {CONFIG_PATH}\n")
