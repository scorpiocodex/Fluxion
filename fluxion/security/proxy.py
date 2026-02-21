"""Proxy detection and configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProxyConfig:
    """Detected proxy settings."""

    http: str | None = None
    https: str | None = None
    no_proxy: list[str] | None = None


class ProxyDetector:
    """Detect system proxy settings from environment."""

    ENV_VARS = {
        "http": ["HTTP_PROXY", "http_proxy"],
        "https": ["HTTPS_PROXY", "https_proxy"],
        "no_proxy": ["NO_PROXY", "no_proxy"],
    }

    @classmethod
    def detect(cls) -> ProxyConfig:
        """Return detected proxy configuration."""
        http_proxy = cls._env_first(cls.ENV_VARS["http"])
        https_proxy = cls._env_first(cls.ENV_VARS["https"])
        no_proxy_raw = cls._env_first(cls.ENV_VARS["no_proxy"])
        no_proxy = (
            [h.strip() for h in no_proxy_raw.split(",") if h.strip()]
            if no_proxy_raw
            else None
        )
        return ProxyConfig(http=http_proxy, https=https_proxy, no_proxy=no_proxy)

    @staticmethod
    def _env_first(keys: list[str]) -> str | None:
        for key in keys:
            val = os.environ.get(key)
            if val:
                return val
        return None

    @classmethod
    def as_httpx_dict(cls, config: ProxyConfig | None = None) -> dict[str, str] | None:
        """Convert to httpx-compatible proxy mapping."""
        cfg = config or cls.detect()
        proxies: dict[str, str] = {}
        if cfg.http:
            proxies["http://"] = cfg.http
        if cfg.https:
            proxies["https://"] = cfg.https
        return proxies or None
