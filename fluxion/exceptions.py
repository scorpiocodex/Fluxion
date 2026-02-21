"""Fluxion exception hierarchy."""

from __future__ import annotations


class FluxionError(Exception):
    """Base exception for all Fluxion errors."""

    def __init__(self, message: str, suggestion: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion


class NetworkError(FluxionError):
    """Raised for network-level failures (DNS, connection, timeout)."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message, suggestion)
        self.status_code = status_code


class SecurityError(FluxionError):
    """Raised for TLS, certificate, or integrity verification failures."""


class InstallerError(FluxionError):
    """Raised when dependency installation or system setup fails."""


class ProtocolError(FluxionError):
    """Raised for protocol-specific failures (HTTP/3, FTP, SFTP)."""


class PluginError(FluxionError):
    """Raised for plugin loading, registration, or execution failures."""


class ConfigError(FluxionError):
    """Raised for configuration parsing or validation errors."""


class ResumeError(FluxionError):
    """Raised when download resume is not supported or fails."""


class StealthError(FluxionError):
    """Raised for stealth/browser impersonation failures."""
