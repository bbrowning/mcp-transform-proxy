# Contributing to MCP Transform Proxy

## Development Setup

```bash
# Clone the repository
git clone https://github.com/bbrowning/mcp-transform-proxy.git
cd mcp-transform-proxy

# Install dependencies (requires uv)
make install

# Run all quality gates (lint, typecheck, test)
make check

# Or run individually
make lint       # ruff check
make typecheck  # mypy
make test       # pytest
```

## Release Process

### 1. Update Version

```bash
make set-version NEW_VERSION=X.Y.Z
```

This updates both `pyproject.toml` and `src/mcp_transform_proxy/__init__.py`.

### 2. Run Quality Gates

```bash
make check
```

All tests, linting, and type checking must pass.

### 3. Build Everything

```bash
# Build Python wheel/sdist and container image
make build

# Or build separately
make build-python     # wheel and sdist only
make build-container  # container image only
```

### 4. Full Release (Recommended)

```bash
make release
```

This runs: `check` → `build` → `tag` → `push-images` → `release-pypi`

### 5. Manual Release Steps (Alternative)

If you need to run steps individually:

```bash
# Create and push git tag
make tag

# Push container images to registry
make push-images

# Upload to PyPI (requires TWINE_USERNAME and TWINE_PASSWORD)
make release-pypi
```

For PyPI authentication:
- Username: `__token__`
- Password: Your PyPI API token (including the `pypi-` prefix)

### 6. Create GitHub Release

1. Go to the GitHub releases page
2. Create a release from the `vX.Y.Z` tag
3. Include release notes describing changes

### Container Registry

By default, images are pushed to `quay.io/bbrowning/mcp-transform-proxy`. Override with:

```bash
make push-images REGISTRY=your-registry.io REPOSITORY=your-org/mcp-transform-proxy
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Run `make check` before submitting PRs (runs lint, typecheck, and tests)
- Install pre-commit hooks: `uv run pre-commit install`
