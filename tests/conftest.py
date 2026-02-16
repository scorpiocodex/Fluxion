"""Shared test fixtures."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncIterator, Iterator

import pytest


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """Return a temporary directory for test outputs."""
    return tmp_path


@pytest.fixture
def sample_url() -> str:
    return "https://httpbin.org/get"


@pytest.fixture
def sample_download_url() -> str:
    return "https://httpbin.org/bytes/1024"
