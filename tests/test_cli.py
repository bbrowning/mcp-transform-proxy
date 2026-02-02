"""Tests for CLI."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from mcp_transform_proxy import __version__
from mcp_transform_proxy.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestCli:
    def test_version(self, runner: CliRunner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_missing_config(self, runner: CliRunner):
        result = runner.invoke(main, [])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_config_not_found(self, runner: CliRunner):
        result = runner.invoke(main, ["--config", "/nonexistent/config.json"])
        assert result.exit_code != 0

    @patch("mcp_transform_proxy.cli.run_proxy")
    def test_loads_config_and_runs(
        self,
        mock_run_proxy: MagicMock,
        runner: CliRunner,
        tmp_config_file,
        minimal_config: dict[str, Any],
    ):
        config_path = tmp_config_file(minimal_config)
        result = runner.invoke(main, ["--config", str(config_path)])
        assert result.exit_code == 0
        mock_run_proxy.assert_called_once()

    @patch("mcp_transform_proxy.cli.run_proxy")
    def test_transport_override(
        self,
        mock_run_proxy: MagicMock,
        runner: CliRunner,
        tmp_config_file,
        minimal_config: dict[str, Any],
    ):
        config_path = tmp_config_file(minimal_config)
        result = runner.invoke(
            main, ["--config", str(config_path), "--transport", "http"]
        )
        assert result.exit_code == 0
        call_args = mock_run_proxy.call_args
        config = call_args[0][0]
        assert config.proxy.transport == "http"

    @patch("mcp_transform_proxy.cli.run_proxy")
    def test_port_override(
        self,
        mock_run_proxy: MagicMock,
        runner: CliRunner,
        tmp_config_file,
        minimal_config: dict[str, Any],
    ):
        config_path = tmp_config_file(minimal_config)
        result = runner.invoke(
            main, ["--config", str(config_path), "--port", "9999"]
        )
        assert result.exit_code == 0
        call_args = mock_run_proxy.call_args
        config = call_args[0][0]
        assert config.proxy.port == 9999

    def test_empty_servers_error(
        self,
        runner: CliRunner,
        tmp_config_file,
    ):
        config_path = tmp_config_file({"mcpServers": {}})
        result = runner.invoke(main, ["--config", str(config_path)])
        assert result.exit_code != 0
        assert "No MCP servers configured" in result.output

    @patch("mcp_transform_proxy.cli.run_proxy")
    def test_short_options(
        self,
        mock_run_proxy: MagicMock,
        runner: CliRunner,
        tmp_config_file,
        minimal_config: dict[str, Any],
    ):
        config_path = tmp_config_file(minimal_config)
        result = runner.invoke(
            main, ["-c", str(config_path), "-t", "http", "-p", "8888"]
        )
        assert result.exit_code == 0
        call_args = mock_run_proxy.call_args
        config = call_args[0][0]
        assert config.proxy.transport == "http"
        assert config.proxy.port == 8888
