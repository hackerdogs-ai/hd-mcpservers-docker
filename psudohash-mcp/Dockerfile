# Psudohash MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Psudohash MCP Server - Password list generator for targeted attacks based on known information"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="psudohash-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies, clone the repo, and set up the script
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/t3l3machus/psudohash.git /opt/psudohash \
    && chmod +x /opt/psudohash/psudohash.py \
    && ln -s /opt/psudohash/psudohash.py /usr/local/bin/psudohash

WORKDIR /app

# Copy requirements and install Python dependencies for the MCP server
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Explicitly install the dependencies Psudohash needs to run
RUN pip install --no-cache-dir tqdm

# Copy application code
COPY mcp_server.py ./

# Create output directory and grant permissions to mcpuser
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app /opt/psudohash

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8287
# Explicitly tell the server where to find the symlinked script
ENV PSUDOHASH_BIN=/usr/local/bin/psudohash

EXPOSE 8287

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]