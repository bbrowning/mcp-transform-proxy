# MCP Transform Proxy - Build and Release Automation

# Configuration
CONTAINER_ENGINE ?= podman
REGISTRY ?= quay.io
REPOSITORY ?= bbrowning/mcp-transform-proxy
VERSION ?= $(shell grep '^version' pyproject.toml | cut -d'"' -f2)
IMG ?= $(REGISTRY)/$(REPOSITORY):$(VERSION)
IMG_LATEST ?= $(REGISTRY)/$(REPOSITORY):latest
PLATFORM ?= linux/amd64

.PHONY: help install test lint typecheck check build build-python build-container \
        tag push-images release-pypi release clean set-version

help:
	@echo "MCP Transform Proxy - Build and Release Targets"
	@echo ""
	@echo "Development:"
	@echo "  make install      - Install dependencies with uv"
	@echo "  make test         - Run pytest"
	@echo "  make lint         - Run ruff linter"
	@echo "  make typecheck    - Run mypy type checker"
	@echo "  make check        - Run all quality gates"
	@echo ""
	@echo "Build:"
	@echo "  make build        - Build Python dist and container"
	@echo "  make build-python - Build wheel and sdist only"
	@echo "  make build-container - Build container image"
	@echo ""
	@echo "Release:"
	@echo "  make set-version NEW_VERSION=X.Y.Z - Update version in all files"
	@echo "  make tag          - Create and push git tag"
	@echo "  make push-images  - Push container images to registry"
	@echo "  make release-pypi - Upload to PyPI via twine"
	@echo "  make release      - Full release (check, build, tag, push, pypi)"
	@echo ""
	@echo "Configuration:"
	@echo "  CONTAINER_ENGINE=$(CONTAINER_ENGINE)"
	@echo "  REGISTRY=$(REGISTRY)"
	@echo "  REPOSITORY=$(REPOSITORY)"
	@echo "  VERSION=$(VERSION)"
	@echo "  IMG=$(IMG)"
	@echo "  PLATFORM=$(PLATFORM)"

# Development targets

install:
	uv sync --extra dev

test:
	uv run pytest

lint:
	uv run ruff check .

typecheck:
	uv run mypy src

check: lint typecheck test
	@echo "All quality gates passed"

# Build targets

build: build-python build-container

build-python:
	uv build
	@echo "Built Python distribution in dist/"

build-container:
	$(CONTAINER_ENGINE) build --platform $(PLATFORM) -t $(IMG) .
	$(CONTAINER_ENGINE) tag $(IMG) $(IMG_LATEST)
	@echo "Built container image: $(IMG)"

# Release targets

set-version:
ifndef NEW_VERSION
	$(error NEW_VERSION is required. Usage: make set-version NEW_VERSION=0.2.0)
endif
	sed -i '' 's/^version = ".*"/version = "$(NEW_VERSION)"/' pyproject.toml
	sed -i '' 's/^__version__ = ".*"/__version__ = "$(NEW_VERSION)"/' src/mcp_transform_proxy/__init__.py
	@echo "Updated version to $(NEW_VERSION)"

tag:
	git tag -a v$(VERSION) -m "Release v$(VERSION)"
	git push origin v$(VERSION)
	@echo "Created and pushed tag v$(VERSION)"

push-images:
	$(CONTAINER_ENGINE) push $(IMG)
	$(CONTAINER_ENGINE) push $(IMG_LATEST)
	@echo "Pushed images to $(REGISTRY)/$(REPOSITORY)"

release-pypi:
	uv run twine upload dist/*
	@echo "Uploaded to PyPI"

release: check build tag push-images release-pypi
	@echo "Release v$(VERSION) complete"

# Multi-arch build helper (manual steps)
build-multiarch:
	@echo "Building multi-arch images..."
	$(CONTAINER_ENGINE) build --platform linux/amd64 -t $(IMG)-amd64 .
	$(CONTAINER_ENGINE) build --platform linux/arm64 -t $(IMG)-arm64 .
	$(CONTAINER_ENGINE) manifest create $(IMG) $(IMG)-amd64 $(IMG)-arm64
	$(CONTAINER_ENGINE) manifest push $(IMG)
	@echo "Multi-arch manifest pushed: $(IMG)"

# Cleanup

clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned build artifacts"
