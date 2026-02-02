"""Pytest configuration and fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def tmp_config_file(tmp_path: Path):
    """Factory fixture to create temporary config files."""

    def _create_config(config_data: dict[str, Any]) -> Path:
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config_data))
        return config_path

    return _create_config


@pytest.fixture
def minimal_config() -> dict[str, Any]:
    """Minimal valid configuration."""
    return {
        "mcpServers": {
            "test": {
                "url": "https://example.com/mcp",
            }
        }
    }


@pytest.fixture
def full_config() -> dict[str, Any]:
    """Full configuration with all options."""
    return {
        "proxy": {
            "name": "TestProxy",
            "transport": "stdio",
            "port": 9000,
        },
        "mcpServers": {
            "weather": {
                "url": "https://weather.example.com/mcp",
                "transport": "sse",
                "tools": {
                    "get_weather": {
                        "name": "check_weather",
                        "description": "Check current weather conditions",
                        "enabled": True,
                        "arguments": {
                            "units": {
                                "default": "metric",
                                "hide": True,
                            },
                            "location": {
                                "name": "city",
                                "description": "City name to check weather for",
                            },
                        },
                    },
                    "internal_debug": {
                        "enabled": False,
                    },
                },
            },
        },
    }
