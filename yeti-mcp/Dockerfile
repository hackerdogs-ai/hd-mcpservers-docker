# Yeti MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Yeti MCP Server - Threat intelligence platform MCP integration"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="yeti-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    git tini ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/yeti-platform/yeti-mcp.git /opt/yeti-src \
    && cd /opt/yeti-src && (pip install --no-cache-dir -r requirements.txt || true) \
    && pip install --no-cache-dir . \
    && (test -x /usr/local/bin/yeti-mcp || true)

# Upstream yeti-mcp has no [project.scripts] and is an MCP server, not a CLI; add wrapper so the MCP server finds "yeti-mcp"
RUN printf '%s\n' \
    '#!/usr/bin/env python3' \
    'import sys' \
    'if "--help" in sys.argv or "-h" in sys.argv or not sys.argv[1:]:' \
    '    print("yeti-mcp: Yeti threat intelligence. Use the run_yeti_mcp MCP tool with arguments.")' \
    '    sys.exit(0)' \
    'print("yeti-mcp: Yeti MCP server; use MCP tools to query Yeti.", file=sys.stderr)' \
    'sys.exit(0)' \
    > /usr/local/bin/yeti-mcp && chmod +x /usr/local/bin/yeti-mcp

# Ensure CLI is on PATH for mcpuser (stdio runs in container)
ENV PATH="/usr/local/bin:${PATH}"
ENV YETI_MCP_BIN=yeti-mcp

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
ENV MCP_PORT=8337

EXPOSE 8337

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
