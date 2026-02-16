"""Terminal layout detection and responsive mode switching."""

from __future__ import annotations

import enum
import os
import shutil
import signal
import sys
from typing import Callable


class LayoutMode(str, enum.Enum):
    MINIMAL = "minimal"      # <60 cols
    COMPACT = "compact"      # 60–90 cols
    STANDARD = "standard"    # 90–130 cols
    FULL = "full"            # 130+ cols


def get_terminal_width() -> int:
    """Return current terminal width in columns."""
    try:
        return shutil.get_terminal_size().columns
    except (ValueError, OSError):
        return 80


def detect_layout(width: int | None = None) -> LayoutMode:
    """Determine the layout mode for the given terminal width."""
    w = width if width is not None else get_terminal_width()
    if w < 60:
        return LayoutMode.MINIMAL
    if w < 90:
        return LayoutMode.COMPACT
    if w < 130:
        return LayoutMode.STANDARD
    return LayoutMode.FULL


def supports_unicode() -> bool:
    """Check if the terminal likely supports Unicode output.

    On Windows, only returns True for known-good modern terminals.
    Rich's LegacyWindowsTerm uses the system codepage (often cp1252)
    which cannot encode Unicode symbols, even if Python reports UTF-8
    as the stdout encoding.
    """
    if sys.platform == "win32":
        # Windows Terminal
        if os.environ.get("WT_SESSION") is not None:
            return True
        # ConEmu
        if os.environ.get("ConEmuPID") is not None:
            return True
        # VS Code integrated terminal, mintty (Git Bash)
        if os.environ.get("TERM_PROGRAM") in ("vscode", "mintty"):
            return True
        # All other Windows terminals: assume legacy (cp1252)
        return False
    return True


def register_resize_handler(callback: Callable[[], None]) -> None:
    """Register a callback for terminal resize events (SIGWINCH on Unix)."""
    if sys.platform != "win32":
        try:
            signal.signal(signal.SIGWINCH, lambda *_: callback())
        except (OSError, ValueError):
            pass
