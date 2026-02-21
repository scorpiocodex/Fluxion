"""Async FTP protocol handler using aioftp."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncIterator
from urllib.parse import urlparse

from fluxion.exceptions import ProtocolError

try:
    import aioftp
except ImportError:
    aioftp = None  # type: ignore[assignment]


class FTPHandler:
    """Async FTP download handler."""

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout

    async def download(
        self,
        url: str,
        output: Path,
        on_chunk: object | None = None,
    ) -> int:
        """Download a file via FTP. Returns bytes downloaded."""
        if aioftp is None:
            raise ProtocolError(
                "aioftp is not installed.",
                suggestion="Install with: pip install aioftp",
            )

        parsed = urlparse(url)
        host = parsed.hostname or ""
        port = parsed.port or 21
        username = parsed.username or "anonymous"
        password = parsed.password or "fluxion@"
        remote_path = parsed.path or "/"

        try:
            async with aioftp.Client.context(
                host, port=port, user=username, password=password
            ) as client:
                if not await client.exists(remote_path):
                    raise ProtocolError(
                        f"Remote path not found: {remote_path}",
                        suggestion="Check the FTP URL path.",
                    )

                stat = await client.stat(remote_path)
                total_size = int(stat.get("size", 0))

                downloaded = 0
                with output.open("wb") as f:
                    async with client.download_stream(remote_path) as stream:
                        async for block in stream.iter_by_block(65536):
                            f.write(block)
                            downloaded += len(block)

                return downloaded

        except aioftp.StatusCodeError as exc:
            raise ProtocolError(
                f"FTP error: {exc}",
                suggestion="Check credentials and path.",
            ) from exc
        except (OSError, asyncio.TimeoutError) as exc:
            raise ProtocolError(
                f"FTP connection error: {exc}",
                suggestion="Check host and port.",
            ) from exc

    async def list_dir(self, url: str) -> list[str]:
        """List files in an FTP directory."""
        if aioftp is None:
            raise ProtocolError("aioftp is not installed.")

        parsed = urlparse(url)
        host = parsed.hostname or ""
        port = parsed.port or 21
        username = parsed.username or "anonymous"
        password = parsed.password or "fluxion@"
        remote_path = parsed.path or "/"

        try:
            async with aioftp.Client.context(
                host, port=port, user=username, password=password
            ) as client:
                entries = []
                async for path, info in client.list(remote_path):
                    entries.append(str(path))
                return entries
        except Exception as exc:
            raise ProtocolError(f"FTP list error: {exc}") from exc
