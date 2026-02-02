# MCP Tool Transform Proxy

A Python CLI that proxies remote MCP servers while applying configurable tool transformations (name, description, arguments). Sits transparently between MCP clients (like Claude Desktop) and remote MCP servers.

## Installation

```bash
pip install mcp-transform-proxy
```

## Quick Start

1. Create a configuration file:

```json
{
  "mcpServers": {
    "myserver": {
      "url": "https://my-mcp-server.example.com/mcp",
      "tools": {
        "original_tool": {
          "description": "Enhanced description with context about when to use this tool"
        }
      }
    }
  }
}
```

2. Run the proxy:

```bash
mcp-transform-proxy --config config.json
```

## Claude Desktop Integration

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "my-proxy": {
      "command": "mcp-transform-proxy",
      "args": ["--config", "/path/to/config.json"]
    }
  }
}
```

## Configuration

### Full Configuration Example

```json
{
  "proxy": {
    "name": "MyToolProxy",
    "transport": "stdio",
    "port": 8080
  },
  "mcpServers": {
    "weather": {
      "url": "https://weather-api.example.com/mcp",
      "transport": "sse",
      "tools": {
        "get_weather": {
          "name": "check_weather",
          "description": "Check current weather. Use when user asks about weather.",
          "arguments": {
            "units": {
              "default": "metric",
              "hide": true
            },
            "location": {
              "name": "city",
              "description": "City name to check"
            }
          }
        },
        "internal_tool": {
          "enabled": false
        }
      }
    }
  }
}
```

### Configuration Reference

#### Proxy Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | "MCP Transform Proxy" | Name of the proxy server |
| `transport` | "stdio" \| "http" | "stdio" | Transport mode |
| `port` | integer | 8080 | HTTP port (only used with http transport) |

#### Server Settings

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | URL of the upstream MCP server |
| `transport` | "streamable-http" \| "sse" | No | Transport for upstream connection |
| `tools` | object | No | Tool transformations (keyed by tool name) |

#### Tool Transformations

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | null | Rename the tool |
| `description` | string | null | Replace tool description |
| `enabled` | boolean | true | Set to false to hide the tool |
| `arguments` | object | {} | Argument transformations |

#### Argument Transformations

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | null | Rename the argument |
| `description` | string | null | Replace argument description |
| `default` | any | null | Set a default value |
| `hide` | boolean | false | Hide argument from clients |

### Tool Name Prefixing

FastMCP's composite proxy automatically prefixes tool names with the server name. For example, if you have a server named `weather` with a tool `get_forecast`, the prefixed name will be `weather_get_forecast`.

When configuring tool transforms, use the **original** tool name (without prefix) in your config - the proxy handles prefixing internally.

## CLI Options

```
Usage: mcp-transform-proxy [OPTIONS]

Options:
  -c, --config PATH      Path to JSON config file (required)
  -t, --transport TEXT   Override transport mode (stdio or http)
  -p, --port INTEGER     Override HTTP port
  --version              Show version
  --help                 Show this message and exit
```

## Development

```bash
# Clone the repository
git clone https://github.com/your-org/mcp-transform-proxy.git
cd mcp-transform-proxy

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy src
```

## License

MIT
