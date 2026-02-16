"""Browser impersonation profiles with realistic header sets."""

from __future__ import annotations

from dataclasses import dataclass

from fluxion.exceptions import StealthError


@dataclass(frozen=True)
class BrowserProfile:
    """A frozen browser impersonation profile."""

    name: str
    user_agent: str
    headers: tuple[tuple[str, str], ...]
    sec_headers: tuple[tuple[str, str], ...]


_PROFILES: dict[str, BrowserProfile] = {
    "chrome": BrowserProfile(
        name="chrome",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        headers=(
            ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"),
            ("Accept-Language", "en-US,en;q=0.9"),
            ("Accept-Encoding", "gzip, deflate, br, zstd"),
            ("Cache-Control", "no-cache"),
            ("Pragma", "no-cache"),
            ("Upgrade-Insecure-Requests", "1"),
        ),
        sec_headers=(
            ("Sec-Ch-Ua", '"Chromium";v="131", "Not_A Brand";v="24", "Google Chrome";v="131"'),
            ("Sec-Ch-Ua-Mobile", "?0"),
            ("Sec-Ch-Ua-Platform", '"Windows"'),
            ("Sec-Fetch-Dest", "document"),
            ("Sec-Fetch-Mode", "navigate"),
            ("Sec-Fetch-Site", "none"),
            ("Sec-Fetch-User", "?1"),
        ),
    ),
    "firefox": BrowserProfile(
        name="firefox",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) "
            "Gecko/20100101 Firefox/134.0"
        ),
        headers=(
            ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
            ("Accept-Language", "en-US,en;q=0.5"),
            ("Accept-Encoding", "gzip, deflate, br, zstd"),
            ("DNT", "1"),
            ("Upgrade-Insecure-Requests", "1"),
            ("Connection", "keep-alive"),
        ),
        sec_headers=(
            ("Sec-Fetch-Dest", "document"),
            ("Sec-Fetch-Mode", "navigate"),
            ("Sec-Fetch-Site", "none"),
            ("Sec-Fetch-User", "?1"),
        ),
    ),
    "edge": BrowserProfile(
        name="edge",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
        ),
        headers=(
            ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"),
            ("Accept-Language", "en-US,en;q=0.9"),
            ("Accept-Encoding", "gzip, deflate, br, zstd"),
            ("Cache-Control", "no-cache"),
            ("Pragma", "no-cache"),
            ("Upgrade-Insecure-Requests", "1"),
        ),
        sec_headers=(
            ("Sec-Ch-Ua", '"Chromium";v="131", "Not_A Brand";v="24", "Microsoft Edge";v="131"'),
            ("Sec-Ch-Ua-Mobile", "?0"),
            ("Sec-Ch-Ua-Platform", '"Windows"'),
            ("Sec-Fetch-Dest", "document"),
            ("Sec-Fetch-Mode", "navigate"),
            ("Sec-Fetch-Site", "none"),
            ("Sec-Fetch-User", "?1"),
        ),
    ),
    "safari": BrowserProfile(
        name="safari",
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/18.2 Safari/605.1.15"
        ),
        headers=(
            ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
            ("Accept-Language", "en-US,en;q=0.9"),
            ("Accept-Encoding", "gzip, deflate, br"),
            ("Connection", "keep-alive"),
        ),
        sec_headers=(
            ("Sec-Fetch-Dest", "document"),
            ("Sec-Fetch-Mode", "navigate"),
            ("Sec-Fetch-Site", "none"),
        ),
    ),
}


def get_profile(name: str) -> BrowserProfile:
    """Return a browser profile by name. Raises StealthError if unknown."""
    profile = _PROFILES.get(name.lower())
    if profile is None:
        available = ", ".join(sorted(_PROFILES))
        raise StealthError(
            f"Unknown browser profile: {name!r}",
            suggestion=f"Available profiles: {available}",
        )
    return profile


def profile_names() -> list[str]:
    """Return sorted list of available profile names."""
    return sorted(_PROFILES)
