"""Tests for proxy creation and tool transforms."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from mcp_transform_proxy.config import (
    ArgTransformConfig,
    Config,
    ServerConfig,
    ToolTransformConfig,
)
from mcp_transform_proxy.proxy import build_tool_transforms, create_proxy_server


class TestBuildToolTransforms:
    def test_empty_tools(self):
        server_config = ServerConfig(url="https://example.com/mcp")
        transforms, disabled = build_tool_transforms("test", server_config)
        assert transforms == {}
        assert disabled == set()

    def test_tool_rename(self):
        server_config = ServerConfig(
            url="https://example.com/mcp",
            tools={
                "old_name": ToolTransformConfig(name="new_name"),
            },
        )
        transforms, disabled = build_tool_transforms("server1", server_config)
        assert "server1_old_name" in transforms
        assert transforms["server1_old_name"].name == "new_name"
        assert disabled == set()

    def test_tool_description(self):
        server_config = ServerConfig(
            url="https://example.com/mcp",
            tools={
                "my_tool": ToolTransformConfig(description="New description"),
            },
        )
        transforms, disabled = build_tool_transforms("test", server_config)
        assert transforms["test_my_tool"].description == "New description"

    def test_tool_disabled(self):
        server_config = ServerConfig(
            url="https://example.com/mcp",
            tools={
                "hidden_tool": ToolTransformConfig(enabled=False),
            },
        )
        transforms, disabled = build_tool_transforms("test", server_config)
        assert "test_hidden_tool" not in transforms
        assert "tool:test_hidden_tool" in disabled

    def test_argument_transforms(self):
        server_config = ServerConfig(
            url="https://example.com/mcp",
            tools={
                "my_tool": ToolTransformConfig(
                    arguments={
                        "old_arg": ArgTransformConfig(
                            name="new_arg",
                            description="Arg description",
                            default="default_val",
                            hide=True,
                        ),
                    },
                ),
            },
        )
        transforms, disabled = build_tool_transforms("test", server_config)
        transform = transforms["test_my_tool"]
        assert transform.arguments is not None
        assert "old_arg" in transform.arguments

        arg_transform = transform.arguments["old_arg"]
        assert arg_transform.name == "new_arg"
        assert arg_transform.description == "Arg description"
        assert arg_transform.default == "default_val"
        assert arg_transform.hide is True

    def test_multiple_tools(self):
        server_config = ServerConfig(
            url="https://example.com/mcp",
            tools={
                "tool1": ToolTransformConfig(name="renamed1"),
                "tool2": ToolTransformConfig(name="renamed2"),
            },
        )
        transforms, disabled = build_tool_transforms("srv", server_config)
        assert len(transforms) == 2
        assert "srv_tool1" in transforms
        assert "srv_tool2" in transforms

    def test_mixed_enabled_disabled(self):
        server_config = ServerConfig(
            url="https://example.com/mcp",
            tools={
                "visible": ToolTransformConfig(name="renamed"),
                "hidden": ToolTransformConfig(enabled=False),
            },
        )
        transforms, disabled = build_tool_transforms("srv", server_config)
        assert "srv_visible" in transforms
        assert "srv_hidden" not in transforms
        assert "tool:srv_hidden" in disabled


class TestCreateProxyServer:
    @patch("mcp_transform_proxy.proxy.create_proxy")
    def test_creates_proxy_with_config(self, mock_create_proxy: MagicMock):
        mock_proxy = MagicMock()
        mock_create_proxy.return_value = mock_proxy

        config = Config.model_validate(
            {
                "proxy": {"name": "TestProxy"},
                "mcpServers": {
                    "weather": {"url": "https://weather.example.com/mcp"},
                },
            }
        )

        result = create_proxy_server(config)

        mock_create_proxy.assert_called_once()
        call_args = mock_create_proxy.call_args
        assert call_args[0][0] == {
            "mcpServers": {"weather": {"url": "https://weather.example.com/mcp"}}
        }
        assert call_args[1]["name"] == "TestProxy"
        assert result == mock_proxy

    @patch("mcp_transform_proxy.proxy.create_proxy")
    def test_adds_transforms_when_configured(self, mock_create_proxy: MagicMock):
        mock_proxy = MagicMock()
        mock_create_proxy.return_value = mock_proxy

        config = Config.model_validate(
            {
                "mcpServers": {
                    "test": {
                        "url": "https://example.com/mcp",
                        "tools": {
                            "my_tool": {"name": "renamed_tool"},
                        },
                    },
                },
            }
        )

        create_proxy_server(config)

        mock_proxy.add_transform.assert_called_once()

    @patch("mcp_transform_proxy.proxy.create_proxy")
    def test_no_transforms_when_no_tools_configured(
        self, mock_create_proxy: MagicMock
    ):
        mock_proxy = MagicMock()
        mock_create_proxy.return_value = mock_proxy

        config = Config.model_validate(
            {
                "mcpServers": {
                    "test": {"url": "https://example.com/mcp"},
                },
            }
        )

        create_proxy_server(config)

        mock_proxy.add_transform.assert_not_called()

    @patch("mcp_transform_proxy.proxy.create_proxy")
    def test_includes_transport_when_specified(self, mock_create_proxy: MagicMock):
        mock_proxy = MagicMock()
        mock_create_proxy.return_value = mock_proxy

        config = Config.model_validate(
            {
                "mcpServers": {
                    "test": {
                        "url": "https://example.com/mcp",
                        "transport": "sse",
                    },
                },
            }
        )

        create_proxy_server(config)

        call_args = mock_create_proxy.call_args
        assert call_args[0][0]["mcpServers"]["test"]["transport"] == "sse"

    @patch("mcp_transform_proxy.proxy.create_proxy")
    def test_multiple_servers(self, mock_create_proxy: MagicMock):
        mock_proxy = MagicMock()
        mock_create_proxy.return_value = mock_proxy

        config = Config.model_validate(
            {
                "mcpServers": {
                    "server1": {"url": "https://server1.example.com/mcp"},
                    "server2": {"url": "https://server2.example.com/mcp"},
                },
            }
        )

        create_proxy_server(config)

        call_args = mock_create_proxy.call_args
        servers = call_args[0][0]["mcpServers"]
        assert len(servers) == 2
        assert "server1" in servers
        assert "server2" in servers

    @patch("mcp_transform_proxy.proxy.create_proxy")
    def test_disables_tools_when_configured(self, mock_create_proxy: MagicMock):
        mock_proxy = MagicMock()
        mock_create_proxy.return_value = mock_proxy

        config = Config.model_validate(
            {
                "mcpServers": {
                    "test": {
                        "url": "https://example.com/mcp",
                        "tools": {
                            "hidden_tool": {"enabled": False},
                        },
                    },
                },
            }
        )

        create_proxy_server(config)

        mock_proxy.disable.assert_called_once()
        call_args = mock_proxy.disable.call_args
        assert "tool:test_hidden_tool" in call_args[1]["keys"]
