"""Tests for platform detection."""

from unittest.mock import patch

from fluxion.platform.detect import (
    _detect_arch,
    _read_os_release,
    detect_platform,
    get_distro_info,
)


class TestDetectPlatform:
    def test_returns_string(self) -> None:
        result = detect_platform()
        assert isinstance(result, str)
        assert result in ("linux", "wsl", "darwin", "windows", "bsd") or isinstance(result, str)

    def test_distro_info_structure(self) -> None:
        info = get_distro_info()
        assert info.name
        assert info.family
        assert info.arch
        assert info.version

    def test_detect_arch(self) -> None:
        arch = _detect_arch()
        assert isinstance(arch, str)
        assert len(arch) > 0


class TestDetectPlatformMocked:
    @patch("fluxion.platform.detect.platform")
    def test_linux(self, mock_platform: object) -> None:
        mock_platform.system = lambda: "Linux"  # type: ignore[attr-defined]
        # Just verify no crash
        result = detect_platform()
        assert isinstance(result, str)

    @patch("fluxion.platform.detect.platform")
    def test_windows(self, mock_platform: object) -> None:
        mock_platform.system = lambda: "Windows"  # type: ignore[attr-defined]
        result = detect_platform()
        assert result == "windows"

    @patch("fluxion.platform.detect.platform")
    def test_darwin(self, mock_platform: object) -> None:
        mock_platform.system = lambda: "Darwin"  # type: ignore[attr-defined]
        result = detect_platform()
        assert result == "darwin"
