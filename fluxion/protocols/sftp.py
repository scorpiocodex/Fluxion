"""Async SFTP/SCP protocol handler using asyncssh."""

from __future__ import annotations

import asyncio
from pathlib import Path
from urllib.parse import urlparse

from fluxion.exceptions import ProtocolError

try:
    import asyncssh
except ImportError:
    asyncssh = None  # type: ignore[assignment]


class SFTPHandler:
    """Async SFTP and SCP handler."""

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout

    async def download_sftp(
        self,
        url: str,
        output: Path,
        known_hosts: object | None = None,
        password: str | None = None,
        key_path: str | None = None,
    ) -> int:
        """Download a file via SFTP. Returns bytes downloaded."""
        if asyncssh is None:
            raise ProtocolError(
                "asyncssh is not installed.",
                suggestion="Install with: pip install asyncssh",
            )

        parsed = urlparse(url)
        host = parsed.hostname or ""
        port = parsed.port or 22
        username = parsed.username or ""
        remote_path = parsed.path or "/"

        connect_kwargs: dict[str, object] = {
            "host": host,
            "port": port,
            "username": username or None,
            "known_hosts": known_hosts,
        }
        if password:
            connect_kwargs["password"] = password
        if key_path:
            connect_kwargs["client_keys"] = [key_path]

        try:
            async with asyncssh.connect(**connect_kwargs) as conn:  # type: ignore[arg-type]
                async with conn.start_sftp_client() as sftp:
                    attrs = await sftp.stat(remote_path)
                    total_size = attrs.size or 0

                    await sftp.get(remote_path, str(output))
                    return output.stat().st_size

        except asyncssh.Error as exc:
            raise ProtocolError(
                f"SFTP error: {exc}",
                suggestion="Check credentials and path.",
            ) from exc
        except (OSError, asyncio.TimeoutError) as exc:
            raise ProtocolError(
                f"SFTP connection error: {exc}",
                suggestion="Check host and port.",
            ) from exc

    async def download_scp(
        self,
        url: str,
        output: Path,
        known_hosts: object | None = None,
        password: str | None = None,
        key_path: str | None = None,
    ) -> int:
        """Download a file via SCP. Returns bytes downloaded."""
        if asyncssh is None:
            raise ProtocolError(
                "asyncssh is not installed.",
                suggestion="Install with: pip install asyncssh",
            )

        parsed = urlparse(url)
        host = parsed.hostname or ""
        port = parsed.port or 22
        username = parsed.username or ""
        remote_path = parsed.path or "/"

        connect_kwargs: dict[str, object] = {
            "host": host,
            "port": port,
            "username": username or None,
            "known_hosts": known_hosts,
        }
        if password:
            connect_kwargs["password"] = password
        if key_path:
            connect_kwargs["client_keys"] = [key_path]

        try:
            async with asyncssh.connect(**connect_kwargs) as conn:  # type: ignore[arg-type]
                await asyncssh.scp(
                    (conn, remote_path),  # type: ignore[arg-type]
                    str(output),
                )
                return output.stat().st_size

        except asyncssh.Error as exc:
            raise ProtocolError(
                f"SCP error: {exc}",
                suggestion="Check credentials and path.",
            ) from exc
        except (OSError, asyncio.TimeoutError) as exc:
            raise ProtocolError(
                f"SCP connection error: {exc}",
                suggestion="Check host and port.",
            ) from exc
