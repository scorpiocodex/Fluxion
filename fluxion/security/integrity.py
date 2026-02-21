"""File integrity verification — SHA-256 checksums and secure temp files."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

from fluxion.exceptions import SecurityError


class IntegrityVerifier:
    """SHA-256 checksum computation and verification."""

    BLOCK_SIZE = 256 * 1024  # 256 KiB

    @staticmethod
    def compute_sha256(path: Path) -> str:
        """Return hex-encoded SHA-256 of a file."""
        h = hashlib.sha256()
        with path.open("rb") as f:
            while chunk := f.read(IntegrityVerifier.BLOCK_SIZE):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def verify(path: Path, expected: str) -> bool:
        """Verify file checksum matches *expected*.  Raises on mismatch."""
        actual = IntegrityVerifier.compute_sha256(path)
        if actual.lower() != expected.lower():
            raise SecurityError(
                f"Integrity check failed for {path.name}. "
                f"Expected {expected}, got {actual}.",
                suggestion="The file may be corrupted or tampered with. Re-download.",
            )
        return True

    @staticmethod
    def incremental() -> _IncrementalHasher:
        """Return a streaming hasher that can be fed chunks."""
        return _IncrementalHasher()


class _IncrementalHasher:
    """Streaming SHA-256 hasher for in-flight verification."""

    def __init__(self) -> None:
        self._hasher = hashlib.sha256()
        self._size = 0

    def update(self, data: bytes) -> None:
        self._hasher.update(data)
        self._size += len(data)

    def hexdigest(self) -> str:
        return self._hasher.hexdigest()

    @property
    def bytes_hashed(self) -> int:
        return self._size


class SecureTempFile:
    """Context manager for creating secure temporary files.

    The file is created with restrictive permissions and removed on exit
    unless ``keep`` is set.
    """

    def __init__(self, suffix: str = ".tmp", directory: Path | None = None) -> None:
        self._suffix = suffix
        self._dir = str(directory) if directory else None
        self._fd: int | None = None
        self._path: Path | None = None

    def __enter__(self) -> Path:
        self._fd, name = tempfile.mkstemp(suffix=self._suffix, dir=self._dir)
        self._path = Path(name)
        import sys
        if sys.platform != "win32":
            try:
                os.chmod(self._fd, 0o600)
            except OSError as exc:
                raise SecurityError(
                    f"Failed to set strict permissions on {self._path}: {exc}",
                    suggestion="Check directory permissions or run as a different user.",
                ) from exc
        return self._path

    def __exit__(self, *exc: object) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError as exc:
                import logging
                logging.getLogger("fluxion.security").warning("Failed to close temp fd: %s", exc)
        if self._path and self._path.exists():
            self._path.unlink(missing_ok=True)
