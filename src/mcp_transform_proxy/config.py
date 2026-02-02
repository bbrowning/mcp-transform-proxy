"""Configuration models for MCP Transform Proxy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class ArgTransformConfig(BaseModel):
    """Configuration for transforming a tool argument."""

    name: str | None = None
    description: str | None = None
    default: Any = None
    hide: bool = False
    required: bool | None = None


class ToolTransformConfig(BaseModel):
    """Configuration for transforming a tool."""

    name: str | None = None
    description: str | None = None
    enabled: bool = True
    arguments: dict[str, ArgTransformConfig] = Field(default_factory=dict)


class ServerConfig(BaseModel):
    """Configuration for an upstream MCP server."""

    url: str
    transport: Literal["streamable-http", "sse"] | None = None
    tools: dict[str, ToolTransformConfig] = Field(default_factory=dict)


class ProxyConfig(BaseModel):
    """Configuration for the proxy server itself."""

    name: str = "MCP Transform Proxy"
    transport: Literal["stdio", "http"] = "stdio"
    port: int = 8080


class Config(BaseModel):
    """Root configuration model."""

    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    mcpServers: dict[str, ServerConfig] = Field(default_factory=dict)


def load_config(path: str | Path) -> Config:
    """Load and validate configuration from a JSON file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open() as f:
        data = json.load(f)

    return Config.model_validate(data)
