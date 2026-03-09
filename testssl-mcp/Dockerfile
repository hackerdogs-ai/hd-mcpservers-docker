# TestSSL MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="TestSSL MCP Server - SSL/TLS configuration testing."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="testssl-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies required by testssl.sh
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    git \
    bsdmainutils \
    dnsutils \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone the official repository to get the script and its custom OpenSSL binaries
RUN git clone --depth 1 https://github.com/drwetter/testssl.sh.git /opt/testssl

# Create a clean symlink for easy access
RUN ln -s /opt/testssl/testssl.sh /usr/local/bin/testssl

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory and grant permissions
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app /opt/testssl

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8279
# Explicitly tell the server where to find the symlinked script
ENV TESTSSL_BIN=/usr/local/bin/testssl

EXPOSE 8279

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]