"""Tests for plugin manager."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from fluxion.exceptions import PluginError
from fluxion.models import PluginMeta
from fluxion.plugins.base import CommandPlugin, FluxionPlugin, ProtocolPlugin
from fluxion.plugins.manager import PluginManager


class TestPluginBase:
    def test_protocol_plugin_is_abstract(self) -> None:
        with pytest.raises(TypeError):
            ProtocolPlugin()  # type: ignore[abstract]

    def test_command_plugin_is_abstract(self) -> None:
        with pytest.raises(TypeError):
            CommandPlugin()  # type: ignore[abstract]


class TestPluginManager:
    def test_list_empty(self, tmp_path: Path) -> None:
        with patch("fluxion.plugins.manager.PLUGIN_REGISTRY", tmp_path / "reg.json"):
            with patch("fluxion.plugins.manager.PLUGIN_DIR", tmp_path / "plugins"):
                mgr = PluginManager()
                assert mgr.list_plugins() == []

    def test_list_with_entries(self, tmp_path: Path) -> None:
        reg = tmp_path / "reg.json"
        reg.write_text(json.dumps([
            {"name": "test", "version": "1.0", "description": "Test plugin"},
        ]))
        with patch("fluxion.plugins.manager.PLUGIN_REGISTRY", reg):
            with patch("fluxion.plugins.manager.PLUGIN_DIR", tmp_path / "plugins"):
                mgr = PluginManager()
                plugins = mgr.list_plugins()
                assert len(plugins) == 1
                assert plugins[0].name == "test"

    def test_remove_plugin(self, tmp_path: Path) -> None:
        reg = tmp_path / "reg.json"
        reg.write_text(json.dumps([
            {"name": "test", "version": "1.0"},
            {"name": "keep", "version": "2.0"},
        ]))
        with patch("fluxion.plugins.manager.PLUGIN_REGISTRY", reg):
            with patch("fluxion.plugins.manager.PLUGIN_DIR", tmp_path / "plugins"):
                mgr = PluginManager()
                mgr.remove("test")
                plugins = mgr.list_plugins()
                assert len(plugins) == 1
                assert plugins[0].name == "keep"

    def test_load_missing_plugin(self, tmp_path: Path) -> None:
        with patch("fluxion.plugins.manager.PLUGIN_DIR", tmp_path / "plugins"):
            mgr = PluginManager()
            with pytest.raises(PluginError, match="Cannot import"):
                mgr.load("nonexistent_xyz")

    def test_get_protocol_handler_none(self, tmp_path: Path) -> None:
        with patch("fluxion.plugins.manager.PLUGIN_DIR", tmp_path / "plugins"):
            mgr = PluginManager()
            assert mgr.get_protocol_handler("s3") is None
