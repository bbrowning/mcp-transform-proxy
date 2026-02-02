"""CLI entry point for MCP Transform Proxy."""

from __future__ import annotations

import sys
from typing import Literal

import click

from mcp_transform_proxy import __version__
from mcp_transform_proxy.config import load_config
from mcp_transform_proxy.proxy import run_proxy


@click.command()
@click.option(
    "--config",
    "-c",
    required=True,
    type=click.Path(exists=True),
    help="Path to JSON config file",
)
@click.option(
    "--transport",
    "-t",
    type=click.Choice(["stdio", "http"]),
    default=None,
    help="Override transport mode (stdio or http)",
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=None,
    help="Override HTTP port (only used with --transport http)",
)
@click.version_option(version=__version__, prog_name="mcp-transform-proxy")
def main(
    config: str,
    transport: Literal["stdio", "http"] | None,
    port: int | None,
) -> None:
    """MCP Tool Transform Proxy - Proxy MCP servers with tool transformations."""
    try:
        cfg = load_config(config)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        sys.exit(1)

    if transport:
        cfg.proxy.transport = transport

    if port:
        cfg.proxy.port = port

    if not cfg.mcpServers:
        click.echo("Error: No MCP servers configured", err=True)
        sys.exit(1)

    run_proxy(cfg)


if __name__ == "__main__":
    main()
