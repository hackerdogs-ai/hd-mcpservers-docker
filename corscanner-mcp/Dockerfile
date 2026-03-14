# CORScanner MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="CORScanner MCP Server - CORS misconfiguration detection tool"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="corscanner-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies, cleanly clone the repo, and set up the script
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/chenjj/CORScanner.git /opt/cors_scan \
    && chmod +x /opt/cors_scan/cors_scan.py \
    && ln -s /opt/cors_scan/cors_scan.py /usr/local/bin/cors_scan

WORKDIR /app

# Copy requirements and install Python dependencies for the MCP server wrapper
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Explicitly install CORScanner's required dependencies so it doesn't fail silently
RUN pip install --no-cache-dir -r /opt/cors_scan/requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory and grant permissions to mcpuser
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app /opt/cors_scan

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8292
# Provide the direct script path to bypass potential shebang issues
ENV CORSCANNER_SCRIPT=/opt/cors_scan/cors_scan.py

EXPOSE 8292

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]