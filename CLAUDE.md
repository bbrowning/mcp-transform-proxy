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

## Code Quality Standards

### Testing Requirements
- Every new feature or bug fix must include tests
- Maintain or improve test coverage (never decrease)
- Tests should be focused and test one thing
- Use pytest fixtures for shared setup

### Code Organization
- Keep functions small and focused (single responsibility)
- Prefer composition over inheritance
- Keep modules cohesive (~300 line soft limit)
- Clear separation between business logic and I/O

### Type Safety
- Full type annotations on all public functions
- Use strict mypy (already configured)
- Prefer explicit types over `Any`

### Refactoring as You Go
- Boy Scout Rule: leave code cleaner than you found it
- Extract duplicated logic into shared functions
- Remove dead code immediately

### Technical Debt Awareness
- Flag tech debt with `# TODO:` comments including context
- Prefer fixing small issues immediately over adding TODOs
- Document workarounds with "why" and "when removable"

### Quality Gates
- All changes must pass: `uv run pytest`, `uv run ruff check .`, `uv run mypy src`
- Pre-commit hooks enforce this automatically
- Install pre-commit hooks: `uv run pre-commit install`

### Refactoring Session Checklist
When doing code review or refactoring, look for:
- Duplicated code
- Long functions (>50 lines)
- Deep nesting (>3 levels)
- Unclear names
- Unused imports/variables
- Missing type hints
- TODO comments that can now be resolved
- Test coverage gaps

Run `uv run ruff check . --statistics` to see issue patterns.
