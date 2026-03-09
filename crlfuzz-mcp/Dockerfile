# ---- Stage 1: Build crlfuzz from source ----
FROM golang:1.24-bookworm AS builder

# Install the latest version of crlfuzz
RUN go install -v github.com/dwisiswant0/crlfuzz/cmd/crlfuzz@latest

# ---- Stage 2: Runtime ----
# CRLFuzz MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="CRLFuzz MCP Server - CRLF injection vulnerability scanner"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="crlfuzz-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy the statically linked binary from the Go builder stage
COPY --from=builder /go/bin/crlfuzz /usr/local/bin/crlfuzz

WORKDIR /app

# Copy requirements and install Python dependencies
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory and set ownership
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8290
# Explicitly tell the server where to find the binary
ENV CRLFUZZ_BIN=/usr/local/bin/crlfuzz

EXPOSE 8290

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]