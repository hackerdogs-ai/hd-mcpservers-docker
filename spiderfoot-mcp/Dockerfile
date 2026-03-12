# SpiderFoot MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="SpiderFoot MCP Server - OSINT automation (200+ modules)."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="spiderfoot-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install SpiderFoot from GitHub (no PyPI package)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git tini ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/smicallef/spiderfoot.git /opt/spiderfoot \
    && pip install --no-cache-dir -r /opt/spiderfoot/requirements.txt \
    && chmod +x /opt/spiderfoot/sf.py \
    && test -f /opt/spiderfoot/sf.py \
    && ln -sf /opt/spiderfoot/sf.py /usr/local/bin/spiderfoot \
    && chown -R mcpuser:mcpuser /opt/spiderfoot
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

# Environment variables (so mcp_server.py finds the binary)
ENV SPIDERFOOT_BIN=/opt/spiderfoot/sf.py
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8257

EXPOSE 8257

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
