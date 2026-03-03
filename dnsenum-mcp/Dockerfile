# dnsenum MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="dnsenum MCP Server - DNS enumeration tool for discovering host information"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="dnsenum-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    perl libnet-dns-perl libxml-libxml-perl git tini ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/fwaeytens/dnsenum.git /opt/dnsenum \
    && chmod +x /opt/dnsenum/*.pl 2>/dev/null || true \
    && ln -sf /opt/dnsenum/dnsenum.pl /usr/local/bin/dnsenum 2>/dev/null; \
    ln -sf /opt/dnsenum/dnsenum /usr/local/bin/dnsenum 2>/dev/null || true

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
ENV MCP_PORT=8304

EXPOSE 8304

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
