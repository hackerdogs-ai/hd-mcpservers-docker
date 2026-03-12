# ZAP Lis MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="ZAP Lis MCP Server - OWASP ZAP integration for web security testing"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="zap-lis-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    git tini ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/LisBerndt/zap-mcp-server.git /opt/zap-lis-src \
    && cd /opt/zap-lis-src && (pip install --no-cache-dir -r requirements.txt || true) \
    && pip install --no-cache-dir .

# Upstream installs "zap-custom-mcp" (not "zap-mcp"); add wrapper so the MCP server finds "zap-mcp"
# Handle --help, -h, -help, and no args so we return immediately instead of starting the server (which would timeout)
RUN printf '%s\n' \
    '#!/bin/sh' \
    'if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ] || [ "$1" = "-help" ]; then' \
    '  echo "zap-mcp: ZAP Custom MCP server. Use the run_zap_mcp MCP tool with arguments."' \
    '  exit 0' \
    'fi' \
    'exec zap-custom-mcp "$@"' \
    > /usr/local/bin/zap-mcp && chmod +x /usr/local/bin/zap-mcp

# Ensure CLI is on PATH for mcpuser (stdio runs in container)
ENV PATH="/usr/local/bin:${PATH}"
ENV ZAP_MCP_BIN=zap-mcp

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
ENV MCP_PORT=8355

EXPOSE 8355

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
