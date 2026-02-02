"""FastMCP proxy creation with tool transformations."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from fastmcp.server import create_proxy
from fastmcp.server.transforms import ToolTransform
from fastmcp.tools.tool_transform import ArgTransformConfig
from fastmcp.tools.tool_transform import ToolTransformConfig as FastMCPToolTransformConfig

from mcp_transform_proxy.config import Config, ServerConfig


def build_tool_transforms(
    server_name: str, server_config: ServerConfig
) -> tuple[dict[str, FastMCPToolTransformConfig], set[str]]:
    """Convert our config to FastMCP ToolTransformConfig objects.

    Tool names are prefixed with the server name by FastMCP's composite proxy,
    so we need to account for that when building the transforms.

    Returns a tuple of (transforms dict, set of disabled tool keys).
    """
    transforms: dict[str, FastMCPToolTransformConfig] = {}
    disabled_tools: set[str] = set()

    for tool_name, tool_config in server_config.tools.items():
        prefixed_name = f"{server_name}_{tool_name}"

        if not tool_config.enabled:
            disabled_tools.add(f"tool:{prefixed_name}")
            continue

        arg_transforms: dict[str, ArgTransformConfig] = {}
        for arg_name, arg_config in tool_config.arguments.items():
            arg_transforms[arg_name] = ArgTransformConfig(
                name=arg_config.name,
                description=arg_config.description,
                default=arg_config.default,
                hide=arg_config.hide,
            )

        transform_config = FastMCPToolTransformConfig(
            name=tool_config.name,
            description=tool_config.description,
            arguments=arg_transforms if arg_transforms else {},
        )
        transforms[prefixed_name] = transform_config

    return transforms, disabled_tools


def create_proxy_server(config: Config) -> FastMCP:
    """Create a composite proxy with transforms applied."""
    mcp_servers_config: dict[str, Any] = {"mcpServers": {}}

    for server_name, server_config in config.mcpServers.items():
        server_entry: dict[str, Any] = {"url": server_config.url}
        if server_config.transport:
            server_entry["transport"] = server_config.transport
        mcp_servers_config["mcpServers"][server_name] = server_entry

    proxy = create_proxy(mcp_servers_config, name=config.proxy.name)

    all_transforms: dict[str, FastMCPToolTransformConfig] = {}
    all_disabled: set[str] = set()

    for server_name, server_config in config.mcpServers.items():
        transforms, disabled = build_tool_transforms(server_name, server_config)
        all_transforms.update(transforms)
        all_disabled.update(disabled)

    if all_transforms:
        proxy.add_transform(ToolTransform(all_transforms))

    if all_disabled:
        proxy.disable(keys=all_disabled)

    return proxy


def run_proxy(config: Config) -> None:
    """Start the proxy server."""
    proxy = create_proxy_server(config)

    if config.proxy.transport == "http":
        proxy.run(transport="http", port=config.proxy.port)
    else:
        proxy.run()
