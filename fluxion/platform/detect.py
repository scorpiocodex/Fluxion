"""OS and distribution detection engine."""

from __future__ import annotations

import platform
import shutil
import struct
import subprocess
import sys
from pathlib import Path

from fluxion.models import DistroInfo

_PACKAGE_MANAGERS: dict[str, list[str]] = {
    "apt": ["apt-get", "apt"],
    "dnf": ["dnf"],
    "pacman": ["pacman"],
    "zypper": ["zypper"],
    "apk": ["apk"],
    "emerge": ["emerge"],
    "nix-env": ["nix-env"],
    "brew": ["brew"],
    "choco": ["choco"],
    "winget": ["winget"],
}

_FAMILY_MAP: dict[str, str] = {
    "ubuntu": "debian",
    "debian": "debian",
    "linuxmint": "debian",
    "pop": "debian",
    "elementary": "debian",
    "fedora": "redhat",
    "rhel": "redhat",
    "centos": "redhat",
    "rocky": "redhat",
    "alma": "redhat",
    "arch": "arch",
    "manjaro": "arch",
    "endeavouros": "arch",
    "opensuse": "suse",
    "sles": "suse",
    "alpine": "alpine",
    "gentoo": "gentoo",
    "void": "void",
    "nixos": "nix",
    "freebsd": "bsd",
    "openbsd": "bsd",
    "netbsd": "bsd",
}

_FAMILY_TO_PM: dict[str, str] = {
    "debian": "apt",
    "redhat": "dnf",
    "arch": "pacman",
    "suse": "zypper",
    "alpine": "apk",
    "gentoo": "emerge",
    "nix": "nix-env",
}


def _detect_arch() -> str:
    machine = platform.machine().lower()
    bits = struct.calcsize("P") * 8
    mapping: dict[str, str] = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
        "armv7l": "armv7l",
    }
    return mapping.get(machine, f"{machine}_{bits}bit")


def _read_os_release() -> dict[str, str]:
    """Parse /etc/os-release into a dict."""
    result: dict[str, str] = {}
    for path in ("/etc/os-release", "/usr/lib/os-release"):
        p = Path(path)
        if p.exists():
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    result[key.strip()] = value.strip().strip('"')
            return result
    return result


def _try_freedesktop() -> dict[str, str]:
    """Try platform.freedesktop_os_release (Python 3.10+)."""
    try:
        return platform.freedesktop_os_release()  # type: ignore[attr-defined]
    except (OSError, AttributeError):
        return {}


def _try_lsb_release() -> dict[str, str]:
    """Fallback: parse lsb_release -a."""
    result: dict[str, str] = {}
    if shutil.which("lsb_release"):
        try:
            out = subprocess.check_output(
                ["lsb_release", "-a"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5,
            )
            for line in out.splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    result[key.strip()] = value.strip()
        except (subprocess.SubprocessError, OSError) as exc:
            import logging
            logging.getLogger("fluxion.platform").debug("lsb_release command failed: %s", exc)
    return result


def _detect_package_manager_probe() -> str:
    """Detect package manager by probing available binaries."""
    for pm_name, binaries in _PACKAGE_MANAGERS.items():
        for binary in binaries:
            if shutil.which(binary):
                return pm_name
    return "unknown"


def _detect_wsl() -> bool:
    """Detect if running inside WSL."""
    if sys.platform != "linux":
        return False
    try:
        version_path = Path("/proc/version")
        if version_path.exists():
            content = version_path.read_text(encoding="utf-8", errors="replace").lower()
            return "microsoft" in content or "wsl" in content
    except OSError as exc:
        import logging
        logging.getLogger("fluxion.platform").debug("Could not read /proc/version: %s", exc)
    return False


def _detect_linux() -> DistroInfo:
    """Detect Linux distribution details."""
    os_info = _try_freedesktop() or _read_os_release() or _try_lsb_release()
    name = os_info.get("ID", os_info.get("Distributor ID", "linux")).lower()
    version = os_info.get("VERSION_ID", os_info.get("Release", "unknown"))
    family = _FAMILY_MAP.get(name, "linux")
    pm = _FAMILY_TO_PM.get(family, _detect_package_manager_probe())

    wsl_suffix = " (WSL)" if _detect_wsl() else ""
    return DistroInfo(
        name=f"{name}{wsl_suffix}",
        family=family,
        version=version,
        package_manager=pm,
        arch=_detect_arch(),
    )


def _detect_macos() -> DistroInfo:
    mac_ver = platform.mac_ver()[0] or "unknown"
    pm = "brew" if shutil.which("brew") else "unknown"
    return DistroInfo(
        name="macOS",
        family="darwin",
        version=mac_ver,
        package_manager=pm,
        arch=_detect_arch(),
    )


def _detect_windows() -> DistroInfo:
    win_ver = platform.version()
    if shutil.which("winget"):
        pm = "winget"
    elif shutil.which("choco"):
        pm = "choco"
    else:
        pm = "unknown"
    return DistroInfo(
        name="Windows",
        family="windows",
        version=win_ver,
        package_manager=pm,
        arch=_detect_arch(),
    )


def _detect_bsd() -> DistroInfo:
    return DistroInfo(
        name=platform.system().lower(),
        family="bsd",
        version=platform.release(),
        package_manager=_detect_package_manager_probe(),
        arch=_detect_arch(),
    )


def detect_platform() -> str:
    """Return a normalised platform key: linux, darwin, windows, bsd."""
    system = platform.system().lower()
    if system == "linux":
        return "wsl" if _detect_wsl() else "linux"
    if system == "darwin":
        return "darwin"
    if system == "windows":
        return "windows"
    if "bsd" in system:
        return "bsd"
    return system


def get_distro_info() -> DistroInfo:
    """Return structured OS / distribution information."""
    plat = detect_platform()
    detectors = {
        "linux": _detect_linux,
        "wsl": _detect_linux,
        "darwin": _detect_macos,
        "windows": _detect_windows,
        "bsd": _detect_bsd,
    }
    detector = detectors.get(plat, _detect_linux)
    return detector()
