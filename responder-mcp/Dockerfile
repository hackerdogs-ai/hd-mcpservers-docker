# Responder MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Responder MCP Server - LLMNR/NBT-NS/MDNS poisoner for credential harvesting."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="responder-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# TODO: Install Responder — add your install steps here.
# Examples:
#   apt:   RUN apt-get update && apt-get install -y --no-install-recommends Responder && rm -rf /var/lib/apt/lists/*
#   pip:   RUN pip install --no-cache-dir Responder
#   go:    (use multi-stage) FROM golang:1.24-bookworm AS builder; RUN go install ...@latest; then COPY --from=builder
#   cargo: (use multi-stage) FROM rust:1.77 AS builder; RUN cargo install Responder; then COPY --from=builder

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    git \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install netifaces in the same Python environment
RUN pip install --no-cache-dir netifaces
RUN pip install --no-cache-dir aioquic

# Install Responder
RUN git clone --depth 1 https://github.com/lgandx/Responder /opt/responder \
    && ln -s /opt/responder/Responder.py /usr/local/bin/Responder \
    && chmod +x /usr/local/bin/Responder

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
ENV MCP_PORT=8207

EXPOSE 8207

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
