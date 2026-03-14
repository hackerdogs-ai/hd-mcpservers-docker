# Nova Proximity MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Nova Proximity MCP Server - Network proximity analysis and threat detection"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="nova-proximity-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies and cleanly clone the repo
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/Nova-Hunting/nova-proximity.git /opt/nova-proximity

WORKDIR /app

# Upgrade pip to handle complex dependency resolution efficiently
RUN pip install --no-cache-dir --upgrade pip

# FIX: We are bypassing the host's requirements.txt to avoid the uvicorn conflict loop.
# We explicitly install fastmcp and nova-hunting together so pip resolves them cleanly.
RUN pip install --no-cache-dir fastmcp "uvicorn>=0.35" nova-hunting

# Safely install Nova Proximity's internal tool requirements
RUN if [ -f "/opt/nova-proximity/requirements.txt" ]; then pip install --no-cache-dir -r /opt/nova-proximity/requirements.txt; fi

# Copy application code (Make sure your mcp_server.py is in the same directory!)
COPY mcp_server.py ./

# Create output directory and grant permissions to mcpuser
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app /opt/nova-proximity

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8298
# Pointing directly to the correct script name
ENV NOVA_PROXIMITY_SCRIPT=/opt/nova-proximity/novaprox.py

EXPOSE 8298

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]