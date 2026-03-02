# Cvemap MCP Server - Hackerdogs Ready
# Multi-stage build: Go builder + Python runtime
# Multi-arch build for linux/amd64 and linux/arm64

# ---- Stage 1: Build cvemap from source ----
FROM golang:1.24-bookworm AS builder

RUN go install github.com/projectdiscovery/cvemap/cmd/cvemap@latest

# ---- Stage 2: Runtime ----
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Cvemap MCP Server - CVE/vulnerability search and analysis"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="cvemap-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy cvemap binary from builder
COPY --from=builder /go/bin/cvemap /usr/local/bin/cvemap

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

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8106

EXPOSE 8106

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
