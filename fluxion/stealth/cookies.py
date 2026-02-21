"""Cookie handling — parse, load, and export cookies for stealth requests."""

from __future__ import annotations

import json
from pathlib import Path

from fluxion.exceptions import StealthError


class CookieJar:
    """Collects cookies from various sources and exports them as headers."""

    def __init__(self) -> None:
        self._cookies: dict[str, str] = {}

    def add_raw(self, raw: str) -> None:
        """Parse ``"name=value"`` or ``"n1=v1; n2=v2"`` into the jar."""
        for part in raw.split(";"):
            part = part.strip()
            if "=" in part:
                name, _, value = part.partition("=")
                name = name.strip()
                value = value.strip()
                if name:
                    self._cookies[name] = value

    def load_file(self, path: Path) -> None:
        """Load cookies from a Netscape cookie-jar file or a JSON export.

        Netscape format: 7 tab-separated fields per line.
        JSON format: list of objects with ``name`` and ``value`` keys.
        """
        if not path.exists():
            raise StealthError(
                f"Cookie file not found: {path}",
                suggestion="Check the path and try again.",
            )

        text = path.read_text(encoding="utf-8")

        if text.lstrip().startswith("[") or text.lstrip().startswith("{"):
            try:
                data = json.loads(text)
                if isinstance(data, list):
                    for entry in data:
                        if isinstance(entry, dict) and "name" in entry and "value" in entry:
                            self._cookies[entry["name"]] = str(entry["value"])
                    return
            except (json.JSONDecodeError, TypeError) as exc:
                raise StealthError(
                    f"Failed to parse JSON cookie file: {exc}",
                    suggestion="Ensure the file contains a valid JSON array of cookie objects.",
                ) from exc

        # Netscape format
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) >= 7:
                name = fields[5]
                value = fields[6]
                if name:
                    self._cookies[name] = value

    def load_browser(self, browser: str, domain: str | None = None) -> None:
        """Import cookies from a browser via rookiepy.

        Raises StealthError if rookiepy is not installed.
        """
        try:
            import rookiepy
        except ImportError:
            raise StealthError(
                "rookiepy is not installed — cannot import browser cookies.",
                suggestion="Install with: pip install 'fluxion[stealth]'",
            )

        browser_lower = browser.lower()
        loader_map: dict[str, object] = {
            "chrome": rookiepy.chrome,
            "firefox": rookiepy.firefox,
            "edge": rookiepy.edge,
            "safari": rookiepy.safari,
        }

        loader = loader_map.get(browser_lower)
        if loader is None:
            available = ", ".join(sorted(loader_map))
            raise StealthError(
                f"Unsupported browser: {browser!r}",
                suggestion=f"Available browsers: {available}",
            )

        try:
            cookie_list = loader(domains=[domain] if domain else None)  # type: ignore[operator]
        except Exception as exc:
            raise StealthError(
                f"Failed to load cookies from {browser}: {exc}",
                suggestion="Ensure the browser is closed and cookies are accessible.",
            ) from exc

        for cookie in cookie_list:
            if isinstance(cookie, dict) and "name" in cookie and "value" in cookie:
                self._cookies[cookie["name"]] = str(cookie["value"])

    def as_header(self) -> str | None:
        """Return the ``Cookie`` header value, or None if empty."""
        if not self._cookies:
            return None
        return "; ".join(f"{k}={v}" for k, v in self._cookies.items())

    def as_dict(self) -> dict[str, str]:
        """Return a copy of all cookies as a dict."""
        return dict(self._cookies)
