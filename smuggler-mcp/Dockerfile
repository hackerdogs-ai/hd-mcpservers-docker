# Smuggler MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Smuggler MCP Server - HTTP request smuggling detection tool"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="smuggler-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies, clone the repo securely, and set up the script
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/defparam/smuggler.git /opt/smuggler \
    && chmod +x /opt/smuggler/smuggler.py \
    && ln -s /opt/smuggler/smuggler.py /usr/local/bin/smuggler

WORKDIR /app

# Copy requirements and install Python dependencies for the MCP server
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Safely install smuggler dependencies if they exist (Smuggler mostly relies on standard libs, but this future-proofs it)
RUN if [ -f "/opt/smuggler/requirements.txt" ]; then pip install --no-cache-dir -r /opt/smuggler/requirements.txt; fi

# Copy application code
COPY mcp_server.py ./

# Create output directory and grant permissions to mcpuser
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app /opt/smuggler

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8291
# Explicitly tell the server where to find the script
ENV SMUGGLER_BIN=/usr/local/bin/smuggler

EXPOSE 8291

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]