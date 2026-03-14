# dnsReaper MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="dnsReaper MCP Server - Subdomain takeover vulnerability scanner via DNS"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="dnsreaper-mcp"
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
    && git clone --depth 1 https://github.com/punk-security/dnsReaper.git /opt/dnsreaper

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 1. Explicitly install dnsReaper's required dependencies FIRST
# (This will install the older, broken version of google-cloud-dns)
RUN pip install --no-cache-dir -r /opt/dnsreaper/requirements.txt

# 2. THEN apply the FIX: Upgrade google-cloud-dns and install setuptools 
# to resolve the Python 3.12 pkg_resources import error permanently
RUN pip install --no-cache-dir --upgrade setuptools "google-cloud-dns>=0.34.0"

# Copy application code
COPY mcp_server.py ./

# Create output directory and grant permissions to mcpuser
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app /opt/dnsreaper

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8293
# Provide the direct script path (it's main.py, not dnsreaper.py!)
ENV DNSREAPER_SCRIPT=/opt/dnsreaper/main.py

EXPOSE 8293

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]