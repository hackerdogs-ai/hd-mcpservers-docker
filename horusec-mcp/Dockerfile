# Horusec MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Horusec MCP Server - Static application security testing (SAST) tool"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="horusec-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl unzip tini ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install horusec: Bypass the flawed install.sh script and fetch the binary directly 
# using architecture detection to perfectly support your multi-arch goals.
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then BIN_ARCH="amd64"; \
    elif [ "$ARCH" = "aarch64" ]; then BIN_ARCH="arm64"; \
    else BIN_ARCH="amd64"; fi && \
    curl -fsSL -o /usr/local/bin/horusec "https://github.com/ZupIT/horusec/releases/latest/download/horusec_linux_${BIN_ARCH}" && \
    chmod +x /usr/local/bin/horusec

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./
COPY hd_fetch.py ./

# Create output directory
RUN mkdir -p /app/output /app/workdir && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8359

EXPOSE 8359

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]