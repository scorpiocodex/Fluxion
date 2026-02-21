"""Tests for exception hierarchy."""

from fluxion.exceptions import (
    ConfigError,
    FluxionError,
    InstallerError,
    NetworkError,
    PluginError,
    ProtocolError,
    ResumeError,
    SecurityError,
)


class TestExceptions:
    def test_fluxion_error(self) -> None:
        exc = FluxionError("test", suggestion="try again")
        assert exc.message == "test"
        assert exc.suggestion == "try again"
        assert str(exc) == "test"

    def test_network_error(self) -> None:
        exc = NetworkError("timeout", status_code=504)
        assert exc.status_code == 504

    def test_security_error(self) -> None:
        exc = SecurityError("bad cert", suggestion="check cert")
        assert exc.suggestion == "check cert"

    def test_installer_error(self) -> None:
        exc = InstallerError("no sudo")
        assert isinstance(exc, FluxionError)

    def test_protocol_error(self) -> None:
        exc = ProtocolError("quic failed")
        assert isinstance(exc, FluxionError)

    def test_plugin_error(self) -> None:
        exc = PluginError("not found")
        assert isinstance(exc, FluxionError)

    def test_config_error(self) -> None:
        exc = ConfigError("invalid")
        assert isinstance(exc, FluxionError)

    def test_resume_error(self) -> None:
        exc = ResumeError("not supported")
        assert isinstance(exc, FluxionError)

    def test_hierarchy(self) -> None:
        # All should be catchable as FluxionError
        errors = [
            NetworkError("a"),
            SecurityError("b"),
            InstallerError("c"),
            ProtocolError("d"),
            PluginError("e"),
            ConfigError("f"),
            ResumeError("g"),
        ]
        for err in errors:
            assert isinstance(err, FluxionError)
            assert isinstance(err, Exception)
