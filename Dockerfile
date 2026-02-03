# Stage 1: Build wheel using uv
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build
COPY pyproject.toml uv.lock README.md ./
COPY src/ src/

RUN uv build --wheel

# Stage 2: Runtime
FROM python:3.12-slim

# Create non-root user for OpenShift compatibility
RUN groupadd -r -g 1001 mcp && useradd -r -u 1001 -g mcp mcp

# Install the wheel
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Create config directory
RUN mkdir -p /config && chown mcp:mcp /config

USER 1001

ENTRYPOINT ["mcp-transform-proxy"]
CMD ["--config", "/config/config.json"]
