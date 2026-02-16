"""Stealth context — assembles final request headers from all stealth sources."""

from __future__ import annotations

from dataclasses import dataclass, field

from fluxion.stealth.cookies import CookieJar
from fluxion.stealth.profiles import BrowserProfile


@dataclass
class StealthContext:
    """Aggregates a browser profile, cookies, custom headers, and referer."""

    profile: BrowserProfile | None = None
    cookie_jar: CookieJar = field(default_factory=CookieJar)
    custom_headers: dict[str, str] = field(default_factory=dict)
    referer: str | None = None

    def build_headers(self) -> dict[str, str]:
        """Merge all sources into a single headers dict.

        Priority (later wins):
            profile base headers → profile sec_fetch headers →
            User-Agent from profile → referer → custom headers → cookies
        """
        headers: dict[str, str] = {}

        if self.profile:
            for name, value in self.profile.headers:
                headers[name] = value
            for name, value in self.profile.sec_headers:
                headers[name] = value
            headers["User-Agent"] = self.profile.user_agent

        if self.referer:
            headers["Referer"] = self.referer

        # Custom headers override everything except cookies
        headers.update(self.custom_headers)

        cookie_header = self.cookie_jar.as_header()
        if cookie_header:
            headers["Cookie"] = cookie_header

        return headers
