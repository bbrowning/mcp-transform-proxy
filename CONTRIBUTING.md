# Contributing to MCP Transform Proxy

## Development Setup

```bash
# Clone the repository
git clone https://github.com/bbrowning/mcp-transform-proxy.git
cd mcp-transform-proxy

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy src
```

## Release Process

### 1. Update Version

Edit `pyproject.toml` and update the version number:

```toml
version = "X.Y.Z"
```

### 2. Build the Package

```bash
# Install build tools if needed
pip install build twine

# Clean previous builds
rm -rf dist/

# Build source distribution and wheel
python -m build
```

This creates:
- `dist/mcp_transform_proxy-X.Y.Z.tar.gz` (source distribution)
- `dist/mcp_transform_proxy-X.Y.Z-py3-none-any.whl` (wheel)

### 3. Test on TestPyPI (Optional)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test install in a fresh environment
pip install --index-url https://test.pypi.org/simple/ mcp-transform-proxy
```

### 4. Publish to PyPI

```bash
twine upload dist/*
```

When prompted:
- Username: `__token__`
- Password: Your PyPI API token (including the `pypi-` prefix)

### 5. Create GitHub Release

1. Tag the release: `git tag vX.Y.Z && git push origin vX.Y.Z`
2. Create a release on GitHub from the tag
3. Include release notes describing changes

## Code Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Run `ruff check .` and `mypy src` before submitting PRs
- All tests must pass (`pytest`)
