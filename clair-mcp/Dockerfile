# Clair MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

# Stage 1: Builder for the Go binaries
FROM golang:1.24-bookworm AS builder
ENV CGO_ENABLED=0
# Build both the clair server daemon and the clairctl CLI scanner
RUN go install github.com/quay/clair/v4/cmd/clair@latest && \
    go install github.com/quay/clair/v4/cmd/clairctl@latest

# Stage 2: Final lightweight Python environment
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Clair MCP Server - Container vulnerability analysis."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="clair-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies (archival tools are heavily used for unpacking container layers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    tar \
    gzip \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy the compiled binaries from the builder stage
COPY --from=builder /go/bin/clair /usr/local/bin/clair
COPY --from=builder /go/bin/clairctl /usr/local/bin/clairctl

# Inject a stub config.yaml using generic container DNS names instead of localhost
RUN mkdir -p /etc/clair && \
    echo 'http_listen_addr: :6060\n\
introspection_addr: :6061\n\
log_level: info\n\
indexer:\n\
  connstring: host=clair-db port=5432 user=clair dbname=clair sslmode=disable\n\
  migrations: true\n\
matcher:\n\
  connstring: host=clair-db port=5432 user=clair dbname=clair sslmode=disable\n\
  migrations: true\n\
notifier:\n\
  connstring: host=clair-db port=5432 user=clair dbname=clair sslmode=disable\n\
  migrations: true' > /etc/clair/config.yaml && \
    chown -R mcpuser:mcpuser /etc/clair

WORKDIR /app

# Copy requirements and install Python dependencies
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8270
# Explicitly tell the server where to find the binaries and the default config
ENV CLAIR_BIN=/usr/local/bin/clair
ENV CLAIRCTL_BIN=/usr/local/bin/clairctl
ENV CLAIR_CONF=/etc/clair/config.yaml

EXPOSE 8270

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]