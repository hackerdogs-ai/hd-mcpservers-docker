# WPScan MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.title="wpscan-mcp"

# 1. Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# 2. Install System Dependencies (Ruby + Build tools for native extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    ruby \
    ruby-dev \
    build-essential \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Install WPScan via RubyGems
RUN gem install wpscan

WORKDIR /app

# 4. Install MCP Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy app and fix permissions (AS ROOT)
COPY mcp_server.py ./
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# 6. Configuration
ENV PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8220
EXPOSE 8220

# 7. Drop privileges
USER mcpuser

# 8. Execution
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
