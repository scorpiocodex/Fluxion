"""HTTP/3 QUIC protocol handler using aioquic."""

from __future__ import annotations

import asyncio
import ssl
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fluxion.exceptions import ProtocolError

try:
    from aioquic.asyncio import connect as quic_connect
    from aioquic.asyncio.protocol import QuicConnectionProtocol
    from aioquic.h3.connection import H3Connection
    from aioquic.h3.events import (
        DataReceived,
        HeadersReceived,
        H3Event,
    )
    from aioquic.quic.configuration import QuicConfiguration

    HAS_QUIC = True
except ImportError:
    HAS_QUIC = False


class QUICHandler:
    """HTTP/3 over QUIC handler."""

    def __init__(self, timeout: float = 30.0, verify: bool = True) -> None:
        self._timeout = timeout
        self._verify = verify

    @staticmethod
    def available() -> bool:
        return HAS_QUIC

    async def fetch(
        self,
        url: str,
        output: Path | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, bytes | None, dict[str, str]]:
        """Perform an HTTP/3 GET request.

        Returns (status_code, body_or_None, response_headers).
        If *output* is given, body is written to file and None is returned.
        """
        if not HAS_QUIC:
            raise ProtocolError(
                "aioquic is not installed.",
                suggestion="Install with: pip install aioquic",
            )

        parsed = urlparse(url)
        host = parsed.hostname or ""
        port = parsed.port or 443
        path = parsed.path or "/"
        if parsed.query:
            path += f"?{parsed.query}"

        configuration = QuicConfiguration(
            is_client=True,
            alpn_protocols=["h3"],
        )

        if not self._verify:
            configuration.verify_mode = ssl.CERT_NONE

        try:
            async with quic_connect(
                host,
                port,
                configuration=configuration,
                create_protocol=_H3ClientProtocol,
            ) as protocol:
                protocol = protocol  # type: QuicConnectionProtocol
                h3_proto: _H3ClientProtocol = protocol  # type: ignore[assignment]

                request_headers = [
                    (b":method", b"GET"),
                    (b":scheme", parsed.scheme.encode()),
                    (b":authority", host.encode()),
                    (b":path", path.encode()),
                    (b"user-agent", b"Fluxion/1.0.0"),
                ]
                if headers:
                    for k, v in headers.items():
                        request_headers.append((k.encode(), v.encode()))

                status, resp_headers, body = await asyncio.wait_for(
                    h3_proto.send_request(request_headers),
                    timeout=self._timeout,
                )

                if output and body:
                    output.write_bytes(body)
                    return status, None, resp_headers

                return status, body, resp_headers

        except asyncio.TimeoutError as exc:
            raise ProtocolError(
                f"HTTP/3 request timed out for {url}",
                suggestion="Server may not support HTTP/3.",
            ) from exc
        except Exception as exc:
            raise ProtocolError(
                f"HTTP/3 error: {exc}",
                suggestion="Verify the server supports HTTP/3 QUIC.",
            ) from exc


if HAS_QUIC:

    class _H3ClientProtocol(QuicConnectionProtocol):
        """Minimal HTTP/3 client protocol."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self._h3: H3Connection | None = None
            self._request_events: dict[int, list[H3Event]] = {}
            self._request_waiters: dict[int, asyncio.Future[None]] = {}

        def quic_event_received(self, event: Any) -> None:
            if self._h3 is None:
                self._h3 = H3Connection(self._quic)

            for h3_event in self._h3.handle_event(event):
                stream_id = getattr(h3_event, "stream_id", None)
                if stream_id is not None:
                    if stream_id not in self._request_events:
                        self._request_events[stream_id] = []
                    self._request_events[stream_id].append(h3_event)

                    if isinstance(h3_event, DataReceived) and h3_event.stream_ended:
                        waiter = self._request_waiters.get(stream_id)
                        if waiter and not waiter.done():
                            waiter.set_result(None)

        async def send_request(
            self, headers: list[tuple[bytes, bytes]]
        ) -> tuple[int, dict[str, str], bytes]:
            """Send request and wait for complete response."""
            if self._h3 is None:
                self._h3 = H3Connection(self._quic)

            stream_id = self._quic.get_next_available_stream_id()
            self._h3.send_headers(stream_id=stream_id, headers=headers, end_stream=True)
            self.transmit()

            waiter: asyncio.Future[None] = asyncio.get_event_loop().create_future()
            self._request_waiters[stream_id] = waiter
            self._request_events[stream_id] = []

            await waiter

            events = self._request_events.pop(stream_id, [])
            self._request_waiters.pop(stream_id, None)

            status = 0
            resp_headers: dict[str, str] = {}
            body = b""

            for evt in events:
                if isinstance(evt, HeadersReceived):
                    for k, v in evt.headers:
                        key = k.decode()
                        val = v.decode()
                        if key == ":status":
                            status = int(val)
                        else:
                            resp_headers[key] = val
                elif isinstance(evt, DataReceived):
                    body += evt.data

            return status, resp_headers, body
