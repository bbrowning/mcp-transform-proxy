"""Tests for configuration loading and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mcp_transform_proxy.config import (
    ArgTransformConfig,
    Config,
    ProxyConfig,
    ServerConfig,
    ToolTransformConfig,
    load_config,
)


class TestArgTransformConfig:
    def test_defaults(self):
        config = ArgTransformConfig()
        assert config.name is None
        assert config.description is None
        assert config.default is None
        assert config.hide is False
        assert config.required is None

    def test_with_values(self):
        config = ArgTransformConfig(
            name="new_name",
            description="New description",
            default="default_value",
            hide=True,
            required=True,
        )
        assert config.name == "new_name"
        assert config.description == "New description"
        assert config.default == "default_value"
        assert config.hide is True
        assert config.required is True


class TestToolTransformConfig:
    def test_defaults(self):
        config = ToolTransformConfig()
        assert config.name is None
        assert config.description is None
        assert config.enabled is True
        assert config.arguments == {}

    def test_with_arguments(self):
        config = ToolTransformConfig(
            name="renamed_tool",
            arguments={
                "arg1": ArgTransformConfig(hide=True),
            },
        )
        assert config.name == "renamed_tool"
        assert "arg1" in config.arguments
        assert config.arguments["arg1"].hide is True


class TestServerConfig:
    def test_minimal(self):
        config = ServerConfig(url="https://example.com/mcp")
        assert config.url == "https://example.com/mcp"
        assert config.transport is None
        assert config.tools == {}

    def test_with_transport(self):
        config = ServerConfig(url="https://example.com/mcp", transport="sse")
        assert config.transport == "sse"

    def test_with_tools(self):
        config = ServerConfig(
            url="https://example.com/mcp",
            tools={
                "tool1": ToolTransformConfig(enabled=False),
            },
        )
        assert "tool1" in config.tools
        assert config.tools["tool1"].enabled is False


class TestProxyConfig:
    def test_defaults(self):
        config = ProxyConfig()
        assert config.name == "MCP Transform Proxy"
        assert config.transport == "stdio"
        assert config.port == 8080

    def test_custom_values(self):
        config = ProxyConfig(name="MyProxy", transport="http", port=9000)
        assert config.name == "MyProxy"
        assert config.transport == "http"
        assert config.port == 9000


class TestConfig:
    def test_defaults(self):
        config = Config()
        assert config.proxy.name == "MCP Transform Proxy"
        assert config.mcpServers == {}

    def test_with_servers(self, minimal_config: dict[str, Any]):
        config = Config.model_validate(minimal_config)
        assert "test" in config.mcpServers
        assert config.mcpServers["test"].url == "https://example.com/mcp"

    def test_full_config(self, full_config: dict[str, Any]):
        config = Config.model_validate(full_config)
        assert config.proxy.name == "TestProxy"
        assert config.proxy.port == 9000
        assert "weather" in config.mcpServers

        weather = config.mcpServers["weather"]
        assert weather.url == "https://weather.example.com/mcp"
        assert weather.transport == "sse"
        assert "get_weather" in weather.tools
        assert weather.tools["get_weather"].name == "check_weather"
        assert weather.tools["get_weather"].arguments["units"].hide is True


class TestLoadConfig:
    def test_load_minimal_config(
        self, tmp_config_file, minimal_config: dict[str, Any]
    ):
        config_path = tmp_config_file(minimal_config)
        config = load_config(config_path)
        assert "test" in config.mcpServers

    def test_load_full_config(self, tmp_config_file, full_config: dict[str, Any]):
        config_path = tmp_config_file(full_config)
        config = load_config(config_path)
        assert config.proxy.name == "TestProxy"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            load_config("/nonexistent/path/config.json")

    def test_invalid_json(self, tmp_path: Path):
        config_path = tmp_path / "bad.json"
        config_path.write_text("not valid json")
        with pytest.raises(json.JSONDecodeError):
            load_config(config_path)

    def test_validation_error(self, tmp_config_file):
        config_path = tmp_config_file(
            {"mcpServers": {"test": {"url": 123}}}  # url should be string
        )
        with pytest.raises(Exception):  # Pydantic ValidationError
            load_config(config_path)
