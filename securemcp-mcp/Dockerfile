# SecureMCP MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64
# Stage 1: build SecureMCP binary with Go 1.21+ (project requires go 1.21)
FROM golang:1.23-bookworm AS builder
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Build static binary; download deps then tidy then build
ENV CGO_ENABLED=0 GOOS=linux
WORKDIR /opt/securemcp
RUN git clone --depth 1 https://github.com/makalin/SecureMCP.git . \
    && sed -i '/\/\/ TODO: Implement response body analysis/i _ = vulnerabilityIndicators' internal/scanner/prompt.go \
    && go mod download \
    && go mod tidy \
    && go build -mod=mod -ldflags="-s -w" -o bin/securemcp ./cmd/securemcp/main.go \
    && test -f bin/securemcp

# Stage 2: runtime image with Python MCP server
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="SecureMCP MCP Server - MCP server security hardening and validation tool"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="securemcp-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install only runtime deps (no golang); copy binary from builder
RUN apt-get update && apt-get install -y --no-install-recommends tini ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /opt/securemcp/bin
COPY --from=builder /opt/securemcp/bin/securemcp /opt/securemcp/bin/securemcp
RUN chown -R mcpuser:mcpuser /opt/securemcp

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables (so mcp_server.py finds the binary — Go binary, not .py)
ENV SECUREMCP_BIN=/opt/securemcp/bin/securemcp
ENV PATH="/opt/securemcp/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8297

EXPOSE 8297

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
