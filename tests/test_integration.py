"""Integration tests for MCP Transform Proxy.

These tests verify that the proxy correctly applies tool transformations
when connecting clients to upstream MCP servers using real subprocess servers.
"""

from __future__ import annotations

import asyncio
import json
import socket
import sys
import textwrap
from pathlib import Path

import pytest
from fastmcp import Client


def find_free_port() -> int:
    """Find an available port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


TEST_SERVER_SCRIPT = textwrap.dedent('''
    """Test MCP server with tools for integration testing."""
    from fastmcp import FastMCP

    server = FastMCP(name="test_backend")

    @server.tool()
    def greet(name: str) -> str:
        """Greet someone by name."""
        return f"Hello, {name}!"

    @server.tool()
    def calculate(a: int, b: int, operation: str = "add") -> int:
        """Perform a calculation."""
        return a + b if operation == "add" else a - b

    @server.tool()
    def internal_debug() -> str:
        """Internal tool to be hidden."""
        return "debug"

    if __name__ == "__main__":
        import sys
        port = int(sys.argv[1])
        server.run(transport="http", port=port)
''')

# Minimal dummy server to trigger FastMCP's composite/prefixing behavior.
# FastMCP only prefixes tools when there are multiple servers in the config.
DUMMY_SERVER_SCRIPT = textwrap.dedent('''
    """Minimal dummy MCP server."""
    from fastmcp import FastMCP

    server = FastMCP(name="dummy")

    @server.tool()
    def ping() -> str:
        """Ping the dummy server."""
        return "pong"

    if __name__ == "__main__":
        import sys
        port = int(sys.argv[1])
        server.run(transport="http", port=port)
''')


async def start_server(
    tmp_path: Path, script: str, name: str
) -> tuple[asyncio.subprocess.Process, str]:
    """Start an MCP server subprocess and wait for it to be ready."""
    port = find_free_port()
    server_script = tmp_path / f"{name}_server.py"
    server_script.write_text(script)

    proc = await asyncio.create_subprocess_exec(
        sys.executable, str(server_script), str(port),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    for _ in range(50):
        await asyncio.sleep(0.1)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("127.0.0.1", port))
                break
        except ConnectionRefusedError:
            continue
    else:
        proc.terminate()
        await proc.wait()
        raise RuntimeError(f"{name} server failed to start")

    return proc, f"http://127.0.0.1:{port}/mcp"


@pytest.fixture
async def test_servers(tmp_path: Path):
    """Start test MCP servers as subprocesses.

    Starts both the main backend server and a dummy server.
    FastMCP only prefixes tools when there are multiple servers in the config,
    so we need at least two servers to test the prefixing behavior.
    """
    backend_proc, backend_url = await start_server(tmp_path, TEST_SERVER_SCRIPT, "backend")
    dummy_proc, dummy_url = await start_server(tmp_path, DUMMY_SERVER_SCRIPT, "dummy")

    yield {"backend": backend_url, "dummy": dummy_url}

    backend_proc.terminate()
    dummy_proc.terminate()
    await backend_proc.wait()
    await dummy_proc.wait()


@pytest.fixture
async def proxy_server(tmp_path: Path, test_servers: dict[str, str]):
    """Start a proxy server connected to the test servers."""
    port = find_free_port()
    config_path = tmp_path / "proxy_config.json"

    def create_config(tools_config: dict | None = None) -> str:
        config = {
            "proxy": {"name": "TestProxy", "transport": "http", "port": port},
            "mcpServers": {
                "backend": {
                    "url": test_servers["backend"],
                    "tools": tools_config or {},
                },
                "dummy": {
                    "url": test_servers["dummy"],
                },
            },
        }
        config_path.write_text(json.dumps(config))
        return f"http://127.0.0.1:{port}/mcp"

    proc = None

    async def start_proxy(tools_config: dict | None = None) -> str:
        nonlocal proc
        url = create_config(tools_config)

        proc = await asyncio.create_subprocess_exec(
            "mcp-transform-proxy", "-c", str(config_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Wait for proxy to be ready
        for _ in range(50):
            await asyncio.sleep(0.1)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(("127.0.0.1", port))
                    break
            except ConnectionRefusedError:
                continue
        else:
            if proc:
                proc.terminate()
                await proc.wait()
            raise RuntimeError("Proxy server failed to start")

        return url

    yield start_proxy

    if proc:
        proc.terminate()
        await proc.wait()


class TestToolPrefixing:
    """Tests verifying tools are prefixed with server name."""

    async def test_tools_prefixed_with_server_name(self, proxy_server):
        proxy_url = await proxy_server()

        async with Client(proxy_url) as client:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]

        # Backend server tools should be prefixed
        assert "backend_greet" in tool_names
        assert "backend_calculate" in tool_names
        assert "backend_internal_debug" in tool_names
        # Dummy server tools should also be prefixed
        assert "dummy_ping" in tool_names
        # Unprefixed names should not exist
        assert "greet" not in tool_names
        assert "ping" not in tool_names


class TestToolRenaming:
    """Tests verifying tool renaming transformations."""

    async def test_tool_renamed(self, proxy_server):
        proxy_url = await proxy_server({"greet": {"name": "say_hello"}})

        async with Client(proxy_url) as client:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]

        assert "say_hello" in tool_names
        assert "backend_greet" not in tool_names

    async def test_renamed_tool_invocation(self, proxy_server):
        proxy_url = await proxy_server({"greet": {"name": "say_hello"}})

        async with Client(proxy_url) as client:
            result = await client.call_tool("say_hello", {"name": "World"})

        assert len(result.content) == 1
        assert result.content[0].text == "Hello, World!"


class TestDescriptionChanges:
    """Tests verifying tool description transformations."""

    async def test_description_changed(self, proxy_server):
        new_desc = "Say hello to someone special"
        proxy_url = await proxy_server({"greet": {"description": new_desc}})

        async with Client(proxy_url) as client:
            tools = await client.list_tools()
            greet_tool = next(t for t in tools if t.name == "backend_greet")

        assert greet_tool.description == new_desc


class TestToolDisabling:
    """Tests verifying tool disabling transformations."""

    async def test_disabled_tool_not_visible(self, proxy_server):
        proxy_url = await proxy_server({"internal_debug": {"enabled": False}})

        async with Client(proxy_url) as client:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]

        assert "backend_internal_debug" not in tool_names
        assert "backend_greet" in tool_names
        assert "backend_calculate" in tool_names


class TestArgumentTransforms:
    """Tests verifying argument transformations."""

    async def test_argument_hidden(self, proxy_server):
        proxy_url = await proxy_server({
            "calculate": {"arguments": {"operation": {"hide": True}}}
        })

        async with Client(proxy_url) as client:
            tools = await client.list_tools()
            calc_tool = next(t for t in tools if t.name == "backend_calculate")

        schema_props = calc_tool.inputSchema.get("properties", {})
        assert "a" in schema_props
        assert "b" in schema_props
        assert "operation" not in schema_props

    async def test_hidden_argument_uses_default(self, proxy_server):
        proxy_url = await proxy_server({
            "calculate": {"arguments": {"operation": {"hide": True, "default": "subtract"}}}
        })

        async with Client(proxy_url) as client:
            result = await client.call_tool("backend_calculate", {"a": 10, "b": 3})

        assert len(result.content) == 1
        assert result.content[0].text == "7"


class TestToolInvocation:
    """Tests verifying tool invocation through the proxy."""

    async def test_prefixed_tool_invocation(self, proxy_server):
        proxy_url = await proxy_server()

        async with Client(proxy_url) as client:
            result = await client.call_tool("backend_greet", {"name": "Alice"})

        assert len(result.content) == 1
        assert result.content[0].text == "Hello, Alice!"

    async def test_calculate_tool_with_default_operation(self, proxy_server):
        proxy_url = await proxy_server()

        async with Client(proxy_url) as client:
            result = await client.call_tool("backend_calculate", {"a": 5, "b": 3})

        assert len(result.content) == 1
        assert result.content[0].text == "8"

    async def test_calculate_tool_with_subtract(self, proxy_server):
        proxy_url = await proxy_server()

        async with Client(proxy_url) as client:
            result = await client.call_tool(
                "backend_calculate", {"a": 10, "b": 4, "operation": "subtract"}
            )

        assert len(result.content) == 1
        assert result.content[0].text == "6"


class TestMultipleTransforms:
    """Tests combining multiple transformations."""

    async def test_rename_and_description_together(self, proxy_server):
        proxy_url = await proxy_server({
            "greet": {"name": "welcome", "description": "Welcome a user warmly"}
        })

        async with Client(proxy_url) as client:
            tools = await client.list_tools()
            welcome_tool = next(t for t in tools if t.name == "welcome")

        assert welcome_tool.description == "Welcome a user warmly"

    async def test_multiple_tools_transformed(self, proxy_server):
        proxy_url = await proxy_server({
            "greet": {"name": "say_hello"},
            "calculate": {"name": "math_op"},
            "internal_debug": {"enabled": False},
        })

        async with Client(proxy_url) as client:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]

        assert "say_hello" in tool_names
        assert "math_op" in tool_names
        assert "backend_internal_debug" not in tool_names
        # 2 backend tools (renamed) + 1 dummy tool
        assert len(tool_names) == 3


class TestArgumentRenaming:
    """Tests verifying argument renaming transformations."""

    async def test_argument_renamed(self, proxy_server):
        proxy_url = await proxy_server({
            "greet": {"arguments": {"name": {"name": "person_name"}}}
        })

        async with Client(proxy_url) as client:
            tools = await client.list_tools()
            greet_tool = next(t for t in tools if t.name == "backend_greet")

        schema_props = greet_tool.inputSchema.get("properties", {})
        assert "person_name" in schema_props
        assert "name" not in schema_props

    async def test_renamed_argument_invocation(self, proxy_server):
        proxy_url = await proxy_server({
            "greet": {"arguments": {"name": {"name": "person_name"}}}
        })

        async with Client(proxy_url) as client:
            result = await client.call_tool("backend_greet", {"person_name": "Bob"})

        assert len(result.content) == 1
        assert result.content[0].text == "Hello, Bob!"
