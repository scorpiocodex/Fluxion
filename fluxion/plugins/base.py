"""Plugin base class and protocol interface."""

from __future__ import annotations

import abc
from pathlib import Path
from typing import Any, AsyncIterator

from fluxion.models import PluginMeta


class FluxionPlugin(abc.ABC):
    """Base class for Fluxion plugins.

    Plugins can register:
    - New protocols (e.g., s3://, gdrive://)
    - New CLI commands
    - Download/upload handlers
    """

    @abc.abstractmethod
    def metadata(self) -> PluginMeta:
        """Return plugin metadata."""
        ...

    def on_load(self) -> None:
        """Called when the plugin is loaded."""

    def on_unload(self) -> None:
        """Called when the plugin is unloaded."""


class ProtocolPlugin(FluxionPlugin):
    """Plugin that adds a new protocol handler."""

    @abc.abstractmethod
    async def download(self, url: str, output: Path, **kwargs: Any) -> int:
        """Download a resource. Returns bytes downloaded."""
        ...

    async def upload(self, local: Path, url: str, **kwargs: Any) -> int:
        """Upload a resource. Returns bytes uploaded."""
        raise NotImplementedError("Upload not supported by this plugin.")

    async def stream(self, url: str, **kwargs: Any) -> AsyncIterator[bytes]:
        """Yield chunks from a streaming resource."""
        raise NotImplementedError("Streaming not supported by this plugin.")
        yield b""  # pragma: no cover


class CommandPlugin(FluxionPlugin):
    """Plugin that adds new CLI commands."""

    @abc.abstractmethod
    def register_commands(self, app: Any) -> None:
        """Register Typer commands on the given app."""
        ...
