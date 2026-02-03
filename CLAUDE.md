# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Tool Transform Proxy is a Python CLI that proxies remote MCP (Model Context Protocol) servers while applying configurable tool transformations. It sits between MCP clients (like Claude Desktop) and remote MCP servers, allowing you to rename tools, modify descriptions, hide arguments, set defaults, and disable tools entirely.

## Development Commands

Always use uv for virtual environment and dependency management.

```bash
# Create a new venv (if needed)
uv venv --python 3.12 --seed

# Install dependencies
uv sync --extra dev

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_config.py

# Run a single test
uv run pytest tests/test_config.py::test_load_config_valid

# Linting
uv run ruff check .

# Type checking
uv run mypy src
```

## Architecture

The codebase has four main modules in `src/mcp_transform_proxy/`:

- **config.py** - Pydantic models for JSON configuration (Config → ProxyConfig + ServerConfig → ToolTransformConfig → ArgTransformConfig). The `load_config()` function validates and parses config files.

- **proxy.py** - Core proxy logic using FastMCP. `build_tool_transforms()` converts our config format to FastMCP's `ToolTransformConfig` objects, handling the server name prefixing that FastMCP applies automatically. `create_proxy_server()` assembles the composite proxy with transforms and disabled tools.

- **cli.py** - Click-based CLI entry point. Loads config, applies CLI overrides, and calls `run_proxy()`.

## Key Implementation Details

- FastMCP's composite proxy prefixes tool names with server names (e.g., `weather_get_forecast`). The config uses unprefixed names; `build_tool_transforms()` adds the prefix.

- Transformations are applied via FastMCP's `ToolTransform` class. Disabled tools use FastMCP's `disable()` method.

- Supports two transport modes: `stdio` (default, for Claude Desktop integration) and `http` (for debugging/testing).
