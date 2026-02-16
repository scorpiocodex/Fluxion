"""Tests for the stealth module — profiles, cookies, context."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fluxion.exceptions import FluxionError, StealthError
from fluxion.stealth.context import StealthContext
from fluxion.stealth.cookies import CookieJar
from fluxion.stealth.profiles import BrowserProfile, get_profile, profile_names


# ---------------------------------------------------------------------------
# BrowserProfiles
# ---------------------------------------------------------------------------


class TestBrowserProfiles:
    def test_chrome_profile_exists(self) -> None:
        profile = get_profile("chrome")
        assert profile.name == "chrome"
        assert "Chrome" in profile.user_agent

    def test_firefox_profile_exists(self) -> None:
        profile = get_profile("firefox")
        assert profile.name == "firefox"
        assert "Firefox" in profile.user_agent

    def test_edge_profile_exists(self) -> None:
        profile = get_profile("edge")
        assert profile.name == "edge"
        assert "Edg" in profile.user_agent

    def test_safari_profile_exists(self) -> None:
        profile = get_profile("safari")
        assert profile.name == "safari"
        assert "Safari" in profile.user_agent

    def test_profile_has_headers(self) -> None:
        profile = get_profile("chrome")
        assert len(profile.headers) > 0
        header_names = [h[0] for h in profile.headers]
        assert "Accept" in header_names

    def test_profile_has_sec_headers(self) -> None:
        profile = get_profile("chrome")
        assert len(profile.sec_headers) > 0
        sec_names = [h[0] for h in profile.sec_headers]
        assert "Sec-Fetch-Dest" in sec_names

    def test_get_profile_case_insensitive(self) -> None:
        profile = get_profile("Chrome")
        assert profile.name == "chrome"

    def test_get_profile_unknown_raises(self) -> None:
        with pytest.raises(StealthError, match="Unknown browser profile"):
            get_profile("netscape")

    def test_profile_names(self) -> None:
        names = profile_names()
        assert "chrome" in names
        assert "firefox" in names
        assert "edge" in names
        assert "safari" in names
        assert names == sorted(names)

    def test_profile_is_frozen(self) -> None:
        profile = get_profile("chrome")
        with pytest.raises(AttributeError):
            profile.name = "modified"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# CookieJar
# ---------------------------------------------------------------------------


class TestCookieJar:
    def test_add_raw_single(self) -> None:
        jar = CookieJar()
        jar.add_raw("session=abc123")
        assert jar.as_dict() == {"session": "abc123"}

    def test_add_raw_multiple_semicolon(self) -> None:
        jar = CookieJar()
        jar.add_raw("a=1; b=2; c=3")
        assert jar.as_dict() == {"a": "1", "b": "2", "c": "3"}

    def test_add_raw_overwrites(self) -> None:
        jar = CookieJar()
        jar.add_raw("key=old")
        jar.add_raw("key=new")
        assert jar.as_dict()["key"] == "new"

    def test_as_header_empty(self) -> None:
        jar = CookieJar()
        assert jar.as_header() is None

    def test_as_header_format(self) -> None:
        jar = CookieJar()
        jar.add_raw("a=1")
        jar.add_raw("b=2")
        header = jar.as_header()
        assert header is not None
        assert "a=1" in header
        assert "b=2" in header
        assert "; " in header

    def test_as_dict_returns_copy(self) -> None:
        jar = CookieJar()
        jar.add_raw("x=1")
        d = jar.as_dict()
        d["x"] = "modified"
        assert jar.as_dict()["x"] == "1"

    def test_load_file_netscape(self, tmp_path: Path) -> None:
        cookie_file = tmp_path / "cookies.txt"
        cookie_file.write_text(
            "# Netscape HTTP Cookie File\n"
            ".example.com\tTRUE\t/\tFALSE\t0\tsession\tabc123\n"
            ".example.com\tTRUE\t/\tFALSE\t0\ttoken\txyz789\n",
            encoding="utf-8",
        )
        jar = CookieJar()
        jar.load_file(cookie_file)
        assert jar.as_dict() == {"session": "abc123", "token": "xyz789"}

    def test_load_file_json(self, tmp_path: Path) -> None:
        cookie_file = tmp_path / "cookies.json"
        data = [
            {"name": "sid", "value": "abc"},
            {"name": "lang", "value": "en"},
        ]
        cookie_file.write_text(json.dumps(data), encoding="utf-8")
        jar = CookieJar()
        jar.load_file(cookie_file)
        assert jar.as_dict() == {"sid": "abc", "lang": "en"}

    def test_load_file_not_found(self, tmp_path: Path) -> None:
        jar = CookieJar()
        with pytest.raises(StealthError, match="Cookie file not found"):
            jar.load_file(tmp_path / "nonexistent.txt")

    def test_load_browser_without_rookiepy(self) -> None:
        jar = CookieJar()
        with pytest.raises(StealthError, match="rookiepy is not installed"):
            jar.load_browser("chrome")


# ---------------------------------------------------------------------------
# StealthContext
# ---------------------------------------------------------------------------


class TestStealthContext:
    def test_build_headers_empty(self) -> None:
        ctx = StealthContext()
        headers = ctx.build_headers()
        assert headers == {}

    def test_build_headers_with_profile(self) -> None:
        profile = get_profile("chrome")
        ctx = StealthContext(profile=profile)
        headers = ctx.build_headers()
        assert "User-Agent" in headers
        assert "Chrome" in headers["User-Agent"]
        assert "Sec-Fetch-Dest" in headers

    def test_custom_headers_override_profile(self) -> None:
        profile = get_profile("chrome")
        ctx = StealthContext(
            profile=profile,
            custom_headers={"User-Agent": "Custom/1.0"},
        )
        headers = ctx.build_headers()
        assert headers["User-Agent"] == "Custom/1.0"

    def test_referer_added(self) -> None:
        ctx = StealthContext(referer="https://google.com")
        headers = ctx.build_headers()
        assert headers["Referer"] == "https://google.com"

    def test_cookies_merged(self) -> None:
        jar = CookieJar()
        jar.add_raw("token=secret")
        ctx = StealthContext(cookie_jar=jar)
        headers = ctx.build_headers()
        assert headers["Cookie"] == "token=secret"

    def test_full_merge_priority(self) -> None:
        profile = get_profile("firefox")
        jar = CookieJar()
        jar.add_raw("sid=123")
        ctx = StealthContext(
            profile=profile,
            cookie_jar=jar,
            custom_headers={"Accept": "application/json"},
            referer="https://example.com",
        )
        headers = ctx.build_headers()
        # Custom overrides profile Accept
        assert headers["Accept"] == "application/json"
        assert headers["Referer"] == "https://example.com"
        assert headers["Cookie"] == "sid=123"
        assert "Firefox" in headers["User-Agent"]


# ---------------------------------------------------------------------------
# StealthError
# ---------------------------------------------------------------------------


class TestStealthError:
    def test_inherits_fluxion_error(self) -> None:
        err = StealthError("test error")
        assert isinstance(err, FluxionError)

    def test_has_suggestion(self) -> None:
        err = StealthError("fail", suggestion="try again")
        assert err.suggestion == "try again"
