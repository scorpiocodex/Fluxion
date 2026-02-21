"""Stateful HTTP caching mechanism for conditional requests."""

from __future__ import annotations

import json
from pathlib import Path

CACHE_DIR = Path.home() / ".fluxion" / "cache"

class HTTPCache:
    """Manages HTTP caching states (ETags and Last-Modified)."""

    def __init__(self) -> None:
        self.directory = CACHE_DIR
        self.db_path = self.directory / "http_cache.json"
        
    def _ensure_dir(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)

    def _load_db(self) -> dict[str, dict[str, str]]:
        if not self.db_path.exists():
            return {}
        try:
            return json.loads(self.db_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_db(self, db: dict[str, dict[str, str]]) -> None:
        self._ensure_dir()
        try:
            self.db_path.write_text(json.dumps(db, indent=2), encoding="utf-8")
        except OSError as exc:
            import logging
            logging.getLogger("fluxion.cache").debug(f"Failed to persist cache state to {self.db_path}: {exc}")

    def get_conditional_headers(self, url: str) -> dict[str, str]:
        """Return headers for a conditional request if cached."""
        db = self._load_db()
        entry = db.get(url)
        if not entry:
            return {}

        headers = {}
        if "etag" in entry:
            headers["If-None-Match"] = entry["etag"]
        if "last_modified" in entry:
            headers["If-Modified-Since"] = entry["last_modified"]
        return headers

    def update_cache(self, url: str, headers: dict[str, str]) -> None:
        """Update cache entry with response headers."""
        etag = headers.get("etag") or headers.get("ETag")
        last_mod = headers.get("last-modified") or headers.get("Last-Modified")

        if not etag and not last_mod:
            return

        db = self._load_db()
        entry = {}
        if etag:
            entry["etag"] = str(etag)
        if last_mod:
            entry["last_modified"] = str(last_mod)

        db[url] = entry
        self._save_db(db)
