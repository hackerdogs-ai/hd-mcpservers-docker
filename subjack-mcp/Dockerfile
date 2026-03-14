# Subjack MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64
# Subjack has no pre-built release assets; build from Go source.

# Stage 1: Builder for the Go binary
FROM golang:1.24-bookworm AS builder
ENV CGO_ENABLED=0
RUN go install github.com/haccer/subjack@latest

# Stage 2: Final lightweight Python environment
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Subjack MCP Server - Subdomain takeover vulnerability checker."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="subjack-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy the compiled subjack binary from the builder stage
COPY --from=builder /go/bin/subjack /usr/local/bin/subjack

# Download fingerprints.json into the exact hardcoded path the Go binary expects
RUN mkdir -p /src/github.com/haccer/subjack && \
    wget -q https://raw.githubusercontent.com/haccer/subjack/master/fingerprints.json -O /src/github.com/haccer/subjack/fingerprints.json && \
    chown -R mcpuser:mcpuser /src

WORKDIR /app

# Copy requirements and install Python dependencies
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory and symlink the fingerprints file into the working dir
RUN mkdir -p /app/output && \
    ln -s /src/github.com/haccer/subjack/fingerprints.json /app/fingerprints.json && \
    chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8260
# Explicitly tell the server where to find the subjack binary and its fingerprints
ENV SUBJACK_BIN=/usr/local/bin/subjack
ENV SUBJACK_FINGERPRINTS=/src/github.com/haccer/subjack/fingerprints.json

EXPOSE 8260

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]