"""TLS inspection, certificate validation, and optional pinning."""

from __future__ import annotations

import ssl
import socket
import datetime
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from fluxion.exceptions import SecurityError


@dataclass(frozen=True)
class CertificateInfo:
    """Parsed TLS certificate details."""

    subject: dict[str, str] = field(default_factory=dict)
    issuer: dict[str, str] = field(default_factory=dict)
    version: int = 0
    serial_number: str = ""
    not_before: str = ""
    not_after: str = ""
    san: list[str] = field(default_factory=list)
    fingerprint_sha256: str = ""
    tls_version: str = ""
    cipher: str = ""


class TLSInspector:
    """Inspect and validate TLS connections."""

    def __init__(
        self,
        verify: bool = True,
        pinned_certs: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._verify = verify
        self._pinned_certs: dict[str, str] = pinned_certs or {}
        self._timeout = timeout

    def inspect(self, url: str) -> CertificateInfo:
        """Connect to *url* and return certificate information."""
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        if parsed.scheme != "https":
            return CertificateInfo()

        ctx = ssl.create_default_context()
        if not self._verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        try:
            with socket.create_connection((hostname, port), timeout=self._timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert: dict[str, Any] = ssock.getpeercert() or {}  # type: ignore[assignment]
                    cipher_info = ssock.cipher() or ("", "", 0)
                    tls_ver = ssock.version() or ""
                    der = ssock.getpeercert(binary_form=True) or b""

                    import hashlib

                    fp = hashlib.sha256(der).hexdigest() if der else ""

                    subject = _parse_dn(cert.get("subject", ()))
                    issuer = _parse_dn(cert.get("issuer", ()))

                    san_raw = cert.get("subjectAltName", ())
                    san = [v for _, v in san_raw]

                    info = CertificateInfo(
                        subject=subject,
                        issuer=issuer,
                        version=cert.get("version", 0),
                        serial_number=cert.get("serialNumber", ""),
                        not_before=cert.get("notBefore", ""),
                        not_after=cert.get("notAfter", ""),
                        san=san,
                        fingerprint_sha256=fp,
                        tls_version=tls_ver,
                        cipher=cipher_info[0],
                    )

                    self._check_pin(hostname, fp)
                    return info

        except ssl.SSLError as exc:
            raise SecurityError(
                f"TLS handshake failed for {hostname}: {exc}",
                suggestion="Check the server certificate or use --no-verify to skip.",
            ) from exc
        except OSError as exc:
            raise SecurityError(
                f"Connection failed for {hostname}:{port}: {exc}",
                suggestion="Verify the host is reachable and the port is correct.",
            ) from exc

    def _check_pin(self, hostname: str, fingerprint: str) -> None:
        expected = self._pinned_certs.get(hostname)
        if expected and expected.lower() != fingerprint.lower():
            raise SecurityError(
                f"Certificate pin mismatch for {hostname}. "
                f"Expected {expected}, got {fingerprint}.",
                suggestion="The server certificate has changed. Verify this is intentional.",
            )

    def check_expiry(self, cert: CertificateInfo, warn_days: int = 30) -> str | None:
        """Return a warning string if certificate expires within *warn_days*."""
        if not cert.not_after:
            return None
        try:
            # OpenSSL date format: 'Sep 14 00:00:00 2025 GMT'
            expiry = datetime.datetime.strptime(cert.not_after, "%b %d %H:%M:%S %Y %Z")
            remaining = (expiry - datetime.datetime.utcnow()).days
            if remaining < 0:
                return f"Certificate EXPIRED {abs(remaining)} days ago"
            if remaining < warn_days:
                return f"Certificate expires in {remaining} days"
        except ValueError:
            pass
        return None


def _parse_dn(dn_tuples: tuple[Any, ...]) -> dict[str, str]:
    """Convert an ssl-style DN tuple-of-tuples to a flat dict."""
    result: dict[str, str] = {}
    for rdn in dn_tuples:
        if isinstance(rdn, tuple):
            for attr in rdn:
                if isinstance(attr, tuple) and len(attr) == 2:
                    result[attr[0]] = attr[1]
    return result
