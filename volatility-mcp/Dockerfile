# Volatility MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Volatility MCP Server - Memory forensics framework."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="volatility-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies
# Install system dependencies (added build-essential for python C-extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    git \
    unzip \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir volatility3

WORKDIR /app

# Copy requirements (Optional now, but good to keep for reference)
COPY requirements.txt ./

# Ignore the unpinned requirements.txt to bypass the v3 ResolutionImpossible bug.
# Explicitly pin fastmcp to the last stable v2 release alongside Volatility 3.
RUN pip install --no-cache-dir "fastmcp==2.14.5" volatility3 pefile capstone

# Copy application code
COPY mcp_server.py ./
COPY hd_fetch.py ./

# Create output directory
RUN mkdir -p /app/output /app/workdir && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8248
# Point to the Volatility 3 binary installed by pip
ENV VOLATILITY_BIN=/usr/local/bin/vol

EXPOSE 8248

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]