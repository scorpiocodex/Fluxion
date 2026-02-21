"""Tests for CLI commands."""

from typer.testing import CliRunner

from fluxion import __version__
from fluxion.cli.app import app

runner = CliRunner()


class TestCLIVersion:
    def test_version(self) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_version_contains_codename(self) -> None:
        result = runner.invoke(app, ["version"])
        assert "Quantum" in result.output


class TestCLIDoctor:
    def test_doctor_runs(self) -> None:
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "Python" in result.output or "python" in result.output.lower()

    def test_doctor_json(self) -> None:
        result = runner.invoke(app, ["doctor", "--json"])
        assert result.exit_code == 0
        assert "version" in result.output

    def test_doctor_shows_checks(self) -> None:
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "OK" in result.output


class TestCLIConfig:
    def test_config_show(self) -> None:
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0

    def test_config_set_invalid_format(self) -> None:
        result = runner.invoke(app, ["config", "--set", "bad_format"])
        assert result.exit_code == 1

    def test_config_set_unknown_key(self) -> None:
        result = runner.invoke(app, ["config", "--set", "nonexistent_key=value"])
        assert result.exit_code == 1


class TestCLIPlugin:
    def test_plugin_list(self) -> None:
        result = runner.invoke(app, ["plugin", "list"])
        assert result.exit_code == 0

    def test_plugin_list_json(self) -> None:
        result = runner.invoke(app, ["plugin", "list", "--json"])
        assert result.exit_code == 0

    def test_plugin_unknown_action(self) -> None:
        result = runner.invoke(app, ["plugin", "unknown"])
        assert result.exit_code == 1

    def test_plugin_install_no_name(self) -> None:
        result = runner.invoke(app, ["plugin", "install"])
        assert result.exit_code == 1

    def test_plugin_remove_no_name(self) -> None:
        result = runner.invoke(app, ["plugin", "remove"])
        assert result.exit_code == 1


class TestCLINoArgs:
    def test_no_args_shows_help(self) -> None:
        result = runner.invoke(app, [])
        assert result.exit_code in (0, 2)
        assert "fluxion" in result.output.lower() or "Usage" in result.output


class TestCLIHelp:
    def test_fetch_help(self) -> None:
        result = runner.invoke(app, ["fetch", "--help"])
        assert result.exit_code == 0
        assert "parallel" in result.output.lower() or "download" in result.output.lower()

    def test_probe_help(self) -> None:
        result = runner.invoke(app, ["probe", "--help"])
        assert result.exit_code == 0

    def test_bench_help(self) -> None:
        result = runner.invoke(app, ["bench", "--help"])
        assert result.exit_code == 0

    def test_secure_help(self) -> None:
        result = runner.invoke(app, ["secure", "--help"])
        assert result.exit_code == 0

    def test_stream_help(self) -> None:
        result = runner.invoke(app, ["stream", "--help"])
        assert result.exit_code == 0


class TestCLIFetchStealthFlags:
    def test_fetch_help_shows_header_flag(self) -> None:
        result = runner.invoke(app, ["fetch", "--help"])
        assert "--header" in result.output
        assert "-H" in result.output

    def test_fetch_help_shows_cookie_flag(self) -> None:
        result = runner.invoke(app, ["fetch", "--help"])
        assert "--cookie" in result.output

    def test_fetch_help_shows_browser_profile(self) -> None:
        result = runner.invoke(app, ["fetch", "--help"])
        assert "--browser-profile" in result.output

    def test_fetch_help_shows_referer(self) -> None:
        result = runner.invoke(app, ["fetch", "--help"])
        assert "--referer" in result.output

    def test_fetch_help_shows_cookie_file(self) -> None:
        result = runner.invoke(app, ["fetch", "--help"])
        assert "--cookie-file" in result.output

    def test_fetch_help_shows_browser_cookies(self) -> None:
        result = runner.invoke(app, ["fetch", "--help"])
        assert "--browser-cookies" in result.output


class TestCLIStreamStealthFlags:
    def test_stream_help_shows_header_flag(self) -> None:
        result = runner.invoke(app, ["stream", "--help"])
        assert "--header" in result.output

    def test_stream_help_shows_browser_profile(self) -> None:
        result = runner.invoke(app, ["stream", "--help"])
        assert "--browser-profile" in result.output
