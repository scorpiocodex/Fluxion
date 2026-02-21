"""Plugin manager — discovery, loading, registration."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

from fluxion.exceptions import PluginError
from fluxion.models import PluginMeta
from fluxion.plugins.base import FluxionPlugin, ProtocolPlugin

PLUGIN_DIR = Path.home() / ".fluxion" / "plugins"
PLUGIN_REGISTRY = Path.home() / ".fluxion" / "plugins.json"


class PluginManager:
    """Manages plugin lifecycle — install, load, unload, list."""

    def __init__(self) -> None:
        self._loaded: dict[str, FluxionPlugin] = {}
        self._protocols: dict[str, ProtocolPlugin] = {}
        PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

    def list_plugins(self) -> list[PluginMeta]:
        """Return metadata for all registered plugins."""
        registry = self._load_registry()
        return [PluginMeta.model_validate(entry) for entry in registry]

    def install(self, name: str) -> None:
        """Install a plugin by name (from PyPI or local)."""
        # For now, install via pip
        import subprocess

        package = f"fluxion-plugin-{name}"
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            raise PluginError(
                f"Failed to install plugin '{name}'.",
                suggestion=f"Check if '{package}' exists on PyPI.",
            )

        # Register in local registry
        meta = PluginMeta(
            name=name,
            version="0.0.0",
            entry_point=f"fluxion_plugin_{name}",
        )
        registry = self._load_registry()
        # Avoid duplicates
        registry = [e for e in registry if e.get("name") != name]
        registry.append(meta.model_dump())
        self._save_registry(registry)

    def remove(self, name: str) -> None:
        """Remove a plugin."""
        registry = self._load_registry()
        registry = [e for e in registry if e.get("name") != name]
        self._save_registry(registry)

        # Unload if loaded
        plugin = self._loaded.pop(name, None)
        if plugin:
            plugin.on_unload()

    def load(self, name: str) -> FluxionPlugin:
        """Load a plugin by name."""
        if name in self._loaded:
            return self._loaded[name]

        entry_point = f"fluxion_plugin_{name}"
        try:
            module = importlib.import_module(entry_point)
        except ImportError as exc:
            raise PluginError(
                f"Cannot import plugin '{name}' (module: {entry_point}).",
                suggestion="Ensure the plugin is installed.",
            ) from exc

        factory = getattr(module, "create_plugin", None)
        if factory is None:
            raise PluginError(
                f"Plugin '{name}' has no create_plugin() factory.",
                suggestion="Plugin must define a create_plugin() function.",
            )

        plugin: FluxionPlugin = factory()
        plugin.on_load()
        self._loaded[name] = plugin

        if isinstance(plugin, ProtocolPlugin):
            meta = plugin.metadata()
            for proto in meta.protocols:
                self._protocols[proto] = plugin

        return plugin

    def get_protocol_handler(self, scheme: str) -> ProtocolPlugin | None:
        """Return the plugin handling a given URL scheme, or None."""
        return self._protocols.get(scheme)

    def _load_registry(self) -> list[dict[str, Any]]:
        if PLUGIN_REGISTRY.exists():
            try:
                return json.loads(PLUGIN_REGISTRY.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
            except (json.JSONDecodeError, OSError) as exc:
                raise PluginError(
                    f"Corrupted plugin registry at {PLUGIN_REGISTRY}: {exc}",
                    suggestion="Fix the JSON file or remove it to reset the registry.",
                ) from exc
        return []

    def _save_registry(self, data: list[dict[str, Any]]) -> None:
        PLUGIN_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
        PLUGIN_REGISTRY.write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8",
        )
