"""fluxion doctor — diagnose installation and environment."""

from __future__ import annotations

import json
import platform
import shutil
import ssl
import sys

from rich.console import Console
from rich.table import Table
from rich import box

from fluxion import __codename__, __version__
from fluxion.hud.panels import QUANTUM_BLUE, QUANTUM_GREEN, QUANTUM_RED, QUANTUM_YELLOW, _icon
from fluxion.platform.detect import get_distro_info


def run_doctor(console: Console, json_output: bool = False) -> None:
    """Run all diagnostic checks."""
    checks: list[dict[str, str]] = []
    icon = _icon()

    # Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 11)
    checks.append({
        "check": "Python version",
        "value": py_ver,
        "status": "ok" if py_ok else "fail",
    })

    # Platform
    distro = get_distro_info()
    checks.append({
        "check": "Platform",
        "value": f"{distro.name} {distro.version} ({distro.arch})",
        "status": "ok",
    })
    checks.append({
        "check": "Package manager",
        "value": distro.package_manager,
        "status": "ok" if distro.package_manager != "unknown" else "warn",
    })

    # TLS
    try:
        ssl_ver = ssl.OPENSSL_VERSION
        checks.append({"check": "OpenSSL", "value": ssl_ver, "status": "ok"})
    except Exception:
        checks.append({"check": "OpenSSL", "value": "unavailable", "status": "fail"})

    # Required packages
    for module, label in [
        ("httpx", "httpx"),
        ("rich", "Rich"),
        ("typer", "Typer"),
        ("pydantic", "Pydantic"),
    ]:
        try:
            mod = __import__(module)
            ver = getattr(mod, "__version__", "?")
            checks.append({"check": label, "value": ver, "status": "ok"})
        except ImportError:
            checks.append({"check": label, "value": "missing", "status": "fail"})

    # Optional packages
    for module, label in [
        ("aioquic", "aioquic (HTTP/3)"),
        ("asyncssh", "asyncssh (SFTP)"),
        ("aioftp", "aioftp (FTP)"),
        ("h2", "h2 (HTTP/2)"),
    ]:
        try:
            mod = __import__(module)
            ver = getattr(mod, "__version__", "?")
            checks.append({"check": label, "value": ver, "status": "ok"})
        except ImportError:
            checks.append({"check": label, "value": "not installed", "status": "warn"})

    # Config directory
    from fluxion.installer.setup import CONFIG_DIR, CACHE_DIR

    checks.append({
        "check": "Config directory",
        "value": str(CONFIG_DIR),
        "status": "ok" if CONFIG_DIR.exists() else "warn",
    })

    if json_output:
        console.print_json(json.dumps({"version": __version__, "checks": checks}))
        return

    console.print(f"\n[{QUANTUM_BLUE}]{icon} FLUXION DOCTOR - v{__version__} [{__codename__}][/{QUANTUM_BLUE}]\n")

    table = Table(show_header=True, header_style=f"bold {QUANTUM_BLUE}", border_style=QUANTUM_BLUE, box=box.HEAVY_EDGE)
    table.add_column("DIAGNOSTIC", min_width=20)
    table.add_column("VALUE")
    table.add_column("STATUS", justify="center")

    status_icons = {
        "ok": f"[{QUANTUM_GREEN}]OK[/{QUANTUM_GREEN}]",
        "warn": f"[{QUANTUM_YELLOW}]!![/{QUANTUM_YELLOW}]",
        "fail": f"[{QUANTUM_RED}]FAIL[/{QUANTUM_RED}]",
    }

    for check in checks:
        table.add_row(
            check["check"],
            check["value"],
            status_icons.get(check["status"], "?"),
        )

    console.print(table)
    console.print()
