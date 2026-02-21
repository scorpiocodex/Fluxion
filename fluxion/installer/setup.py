"""fluxion init — system detection, dependency installation, environment setup."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from fluxion.exceptions import InstallerError
from fluxion.hud.panels import QUANTUM_BLUE, QUANTUM_GREEN, QUANTUM_RED, QUANTUM_YELLOW, _icon
from fluxion.installer.privilege import is_root, run_elevated
from fluxion.platform.detect import detect_platform, get_distro_info

# System-level packages needed for optional features
_SYSTEM_DEPS: dict[str, dict[str, list[str]]] = {
    "apt": {
        "tls": ["ca-certificates", "openssl"],
        "build": ["build-essential", "python3-dev"],
    },
    "dnf": {
        "tls": ["ca-certificates", "openssl"],
        "build": ["gcc", "python3-devel"],
    },
    "pacman": {
        "tls": ["ca-certificates", "openssl"],
        "build": ["base-devel", "python"],
    },
    "zypper": {
        "tls": ["ca-certificates", "openssl"],
        "build": ["gcc", "python3-devel"],
    },
    "apk": {
        "tls": ["ca-certificates", "openssl"],
        "build": ["build-base", "python3-dev"],
    },
    "brew": {
        "tls": ["openssl"],
        "build": [],
    },
    "choco": {
        "tls": [],
        "build": [],
    },
    "winget": {
        "tls": [],
        "build": [],
    },
}

_PM_INSTALL: dict[str, list[str]] = {
    "apt": ["apt-get", "install", "-y"],
    "dnf": ["dnf", "install", "-y"],
    "pacman": ["pacman", "-S", "--noconfirm"],
    "zypper": ["zypper", "install", "-y"],
    "apk": ["apk", "add"],
    "brew": ["brew", "install"],
    "choco": ["choco", "install", "-y"],
    "winget": ["winget", "install", "--accept-package-agreements"],
    "emerge": ["emerge"],
    "nix-env": ["nix-env", "-iA"],
}

CONFIG_DIR = Path.home() / ".fluxion"
CACHE_DIR = CONFIG_DIR / "cache"


async def run_init(console: Console) -> None:
    """Execute the full init sequence."""
    icon = _icon()

    # Step 1: Detect platform
    console.print(f"\n[{QUANTUM_BLUE}]{icon} Detecting platform...[/{QUANTUM_BLUE}]")
    distro = get_distro_info()

    table = Table.grid(padding=(0, 2))
    table.add_column(style="dim", min_width=16)
    table.add_column()
    table.add_row("OS", distro.name)
    table.add_row("FAMILY", distro.family)
    table.add_row("VERSION", distro.version)
    table.add_row("ARCH", distro.arch)
    table.add_row("PACKAGE MANAGER", distro.package_manager)
    table.add_row("PRIVILEGES", "root" if is_root() else "user")
    console.print(table)

    # Step 2: Create config directory
    console.print(f"\n[{QUANTUM_BLUE}]{icon} Setting up directories...[/{QUANTUM_BLUE}]")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    console.print(f"  [{QUANTUM_GREEN}]+[/{QUANTUM_GREEN}] Config: {CONFIG_DIR}")
    console.print(f"  [{QUANTUM_GREEN}]+[/{QUANTUM_GREEN}] Cache:  {CACHE_DIR}")

    # Step 2.5: Validate environment
    console.print(f"\n[{QUANTUM_BLUE}]{icon} Validating environment parameters...[/{QUANTUM_BLUE}]")
    _check_python_version(console)
    _check_disk_space(console, CONFIG_DIR)

    # Step 3: Check Python dependencies
    console.print(f"\n[{QUANTUM_BLUE}]{icon} Checking Python dependencies...[/{QUANTUM_BLUE}]")
    _check_python_deps(console)

    # Step 4: Install system dependencies if applicable
    pm = distro.package_manager
    if pm in _SYSTEM_DEPS and pm in _PM_INSTALL:
        console.print(f"\n[{QUANTUM_BLUE}]{icon} Checking system dependencies...[/{QUANTUM_BLUE}]")
        deps = _SYSTEM_DEPS[pm]
        all_packages: list[str] = []
        for group_packages in deps.values():
            all_packages.extend(group_packages)

        missing = _find_missing_system_packages(all_packages, pm)
        if missing:
            console.print(
                f"  [{QUANTUM_YELLOW}]![/{QUANTUM_YELLOW}] Missing: {', '.join(missing)}"
            )
            console.print(f"  [{QUANTUM_BLUE}]Installing...[/{QUANTUM_BLUE}]")
            try:
                install_cmd = _PM_INSTALL[pm] + missing
                run_elevated(install_cmd)
                console.print(f"  [{QUANTUM_GREEN}]+[/{QUANTUM_GREEN}] System dependencies installed")
            except (subprocess.CalledProcessError, InstallerError) as exc:
                console.print(
                    f"  [{QUANTUM_RED}]X[/{QUANTUM_RED}] Failed: {exc}\n"
                    f"  [{QUANTUM_YELLOW}]You may need to install manually.[/{QUANTUM_YELLOW}]"
                )
        else:
            console.print(f"  [{QUANTUM_GREEN}]+[/{QUANTUM_GREEN}] All system dependencies present")

    # Step 5: Verify TLS
    console.print(f"\n[{QUANTUM_BLUE}]{icon} Verifying TLS configuration...[/{QUANTUM_BLUE}]")
    try:
        import ssl
        import certifi

        ctx = ssl.create_default_context(cafile=certifi.where())
        console.print(f"  [{QUANTUM_GREEN}]+[/{QUANTUM_GREEN}] TLS certificates OK")
    except Exception as exc:
        console.print(f"  [{QUANTUM_RED}]X[/{QUANTUM_RED}] TLS issue: {exc}")

    console.print(
        f"\n[{QUANTUM_GREEN}]{icon} Fluxion initialization complete.[/{QUANTUM_GREEN}]\n"
    )

def _check_python_version(console: Console) -> None:
    """Check that Python version meets minimum requirements."""
    if sys.version_info >= (3, 10):
        console.print(f"  [{QUANTUM_GREEN}]+[/{QUANTUM_GREEN}] Python version OK ({sys.version.split()[0]})")
    else:
        console.print(f"  [{QUANTUM_RED}]X[/{QUANTUM_RED}] Python 3.10+ required. Current: {sys.version.split()[0]}")

def _check_disk_space(console: Console, path: Path) -> None:
    """Verify sufficient disk space is available for operations."""
    try:
        total, used, free = shutil.disk_usage(path)
        # Require at least 500MB free space
        if free < 500 * 1024 * 1024:
            console.print(f"  [{QUANTUM_RED}]X[/{QUANTUM_RED}] Insufficient disk space. Need at least 500MB.")
        else:
            free_gb = free / (1024**3)
            console.print(f"  [{QUANTUM_GREEN}]+[/{QUANTUM_GREEN}] Disk capacity OK ({free_gb:.1f} GB free)")
    except OSError as exc:
        console.print(f"  [{QUANTUM_YELLOW}]![/{QUANTUM_YELLOW}] Could not verify disk space: {exc}")


def _check_python_deps(console: Console) -> None:
    """Check that required Python packages are importable."""
    deps = {
        "httpx": "httpx",
        "rich": "rich",
        "typer": "typer",
        "pydantic": "pydantic",
        "aioquic": "aioquic (HTTP/3 support)",
        "asyncssh": "asyncssh (SFTP/SCP support)",
        "aioftp": "aioftp (FTP support)",
    }
    for module, label in deps.items():
        try:
            __import__(module)
            console.print(f"  [{QUANTUM_GREEN}]+[/{QUANTUM_GREEN}] {label}")
        except ImportError:
            console.print(f"  [{QUANTUM_YELLOW}]![/{QUANTUM_YELLOW}] {label} — not installed")


def _find_missing_system_packages(packages: list[str], pm: str) -> list[str]:
    """Check which system packages are not installed."""
    missing: list[str] = []
    for pkg in packages:
        # Simple heuristic: check if a binary or library exists
        if not shutil.which(pkg):
            missing.append(pkg)
    return missing
