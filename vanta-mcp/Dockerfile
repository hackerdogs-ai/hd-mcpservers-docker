# Vanta MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Vanta MCP Server - Vanta compliance and security monitoring MCP integration"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="vanta-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and stub
COPY mcp_server.py ./
COPY vanta-mcp-stub.py ./

# Install stub as vanta-mcp so the MCP server finds a binary (Vanta requires API credentials for real use)
RUN cp /app/vanta-mcp-stub.py /usr/local/bin/vanta-mcp && \
    sed -i 's/\r$//' /usr/local/bin/vanta-mcp && \
    chmod +x /usr/local/bin/vanta-mcp

# Create output directory
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8348

EXPOSE 8348

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
