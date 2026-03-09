# JWT-Tool MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="JWT-Tool MCP Server - JWT testing and algorithm confusion."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="jwt-tool-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies, including git to clone the repository
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone the JWT-Tool repository directly from GitHub
RUN git clone --depth 1 https://github.com/ticarpi/jwt_tool.git /opt/jwt_tool && \
    chmod +x /opt/jwt_tool/jwt_tool.py && \
    ln -s /opt/jwt_tool/jwt_tool.py /usr/local/bin/jwt_tool.py

WORKDIR /app

# Copy requirements and install Python dependencies
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install JWT-Tool's specific Python dependencies
RUN pip install --no-cache-dir -r /opt/jwt_tool/requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory and grant permissions to the jwt_tool folder
RUN mkdir -p /app/output && \
    chown -R mcpuser:mcpuser /app /opt/jwt_tool

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8265
# Explicitly tell the server where to find the jwt_tool.py script
ENV JWT_TOOL_BIN=/usr/local/bin/jwt_tool.py

EXPOSE 8265

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]