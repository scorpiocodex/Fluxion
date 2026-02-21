"""Tests for security subsystem."""

import os
import tempfile
from pathlib import Path

import pytest

from fluxion.exceptions import SecurityError
from fluxion.security.integrity import IntegrityVerifier, SecureTempFile, _IncrementalHasher
from fluxion.security.proxy import ProxyConfig, ProxyDetector


class TestIntegrityVerifier:
    def test_compute_sha256(self, tmp_path: Path) -> None:
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        sha = IntegrityVerifier.compute_sha256(f)
        assert isinstance(sha, str)
        assert len(sha) == 64

    def test_verify_success(self, tmp_path: Path) -> None:
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        sha = IntegrityVerifier.compute_sha256(f)
        assert IntegrityVerifier.verify(f, sha) is True

    def test_verify_failure(self, tmp_path: Path) -> None:
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        with pytest.raises(SecurityError, match="Integrity check failed"):
            IntegrityVerifier.verify(f, "0" * 64)

    def test_incremental_hasher(self) -> None:
        h = IntegrityVerifier.incremental()
        h.update(b"hello ")
        h.update(b"world")
        assert h.bytes_hashed == 11
        assert len(h.hexdigest()) == 64


class TestSecureTempFile:
    def test_creates_and_cleans_up(self) -> None:
        with SecureTempFile(suffix=".test") as path:
            assert path.exists()
            path.write_bytes(b"secret")
            temp_path = path
        assert not temp_path.exists()

    def test_custom_directory(self, tmp_path: Path) -> None:
        with SecureTempFile(suffix=".test", directory=tmp_path) as path:
            assert str(tmp_path) in str(path)


class TestProxyDetector:
    def test_detect_no_proxy(self) -> None:
        # Clear env
        env_backup = {}
        for key in ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "NO_PROXY"]:
            env_backup[key] = os.environ.pop(key, None)

        try:
            config = ProxyDetector.detect()
            assert config.http is None
            assert config.https is None
        finally:
            for key, val in env_backup.items():
                if val is not None:
                    os.environ[key] = val

    def test_detect_with_proxy(self) -> None:
        os.environ["HTTP_PROXY"] = "http://proxy:8080"
        try:
            config = ProxyDetector.detect()
            assert config.http == "http://proxy:8080"
        finally:
            os.environ.pop("HTTP_PROXY", None)

    def test_as_httpx_dict(self) -> None:
        config = ProxyConfig(http="http://p:80", https="http://p:443")
        result = ProxyDetector.as_httpx_dict(config)
        assert result is not None
        assert "http://" in result
        assert "https://" in result

    def test_as_httpx_dict_empty(self) -> None:
        config = ProxyConfig()
        result = ProxyDetector.as_httpx_dict(config)
        assert result is None
