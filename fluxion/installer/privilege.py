"""Privilege escalation — cross-platform root/admin detection and elevation."""

from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys

from fluxion.exceptions import InstallerError


def is_root() -> bool:
    """Check if the current process has root/admin privileges."""
    if sys.platform == "win32":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            return False
    try:
        return os.geteuid() == 0  # type: ignore[attr-defined]
    except AttributeError:
        return False


def escalate_posix(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command with sudo on Linux/macOS.

    If already root, runs directly. Otherwise prepends sudo.
    """
    if is_root():
        return subprocess.run(command, check=True, text=True, capture_output=True)

    if not shutil.which("sudo"):
        raise InstallerError(
            "sudo not found and not running as root.",
            suggestion="Run Fluxion as root or install sudo.",
        )

    return subprocess.run(
        ["sudo", *command],
        check=True,
        text=True,
        capture_output=True,
    )


def escalate_windows() -> None:
    """Re-launch the current script with UAC elevation on Windows.

    This function does not return — it launches an elevated process and exits.
    """
    if is_root():
        return

    try:
        script = sys.argv[0]
        params = " ".join(sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        sys.exit(0)
    except (AttributeError, OSError) as exc:
        raise InstallerError(
            f"Failed to elevate privileges: {exc}",
            suggestion="Right-click and run as Administrator.",
        ) from exc


def run_elevated(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command with elevated privileges, cross-platform."""
    if sys.platform == "win32":
        if not is_root():
            escalate_windows()
        return subprocess.run(command, check=True, text=True, capture_output=True)
    return escalate_posix(command)
