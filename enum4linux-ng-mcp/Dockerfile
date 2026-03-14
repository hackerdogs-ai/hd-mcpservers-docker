# Enum4linux-ng MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Enum4linux-ng MCP Server - Advanced SMB enumeration with enhanced logging."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="enum4linux-ng-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# TODO: Install enum4linux-ng — add your install steps here.
# Examples:
#   apt:   RUN apt-get update && apt-get install -y --no-install-recommends enum4linux-ng && rm -rf /var/lib/apt/lists/*
#   pip:   RUN pip install --no-cache-dir enum4linux-ng
#   go:    (use multi-stage) FROM golang:1.24-bookworm AS builder; RUN go install ...@latest; then COPY --from=builder
#   cargo: (use multi-stage) FROM rust:1.77 AS builder; RUN cargo install enum4linux-ng; then COPY --from=builder

# Install dependencies for enum4linux-ng
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    samba \
    smbclient \
    ldap-utils \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir impacket \
    && git clone https://github.com/cddmp/enum4linux-ng.git /opt/enum4linux-ng \
    && sed -i '1s|.*|#!/usr/bin/env python3|' /opt/enum4linux-ng/enum4linux-ng.py \
    && ln -s /opt/enum4linux-ng/enum4linux-ng.py /usr/local/bin/enum4linux-ng \
    && chmod +x /usr/local/bin/enum4linux-ng

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
ENV MCP_PORT=8210

EXPOSE 8210

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "-u", "mcp_server.py"]
