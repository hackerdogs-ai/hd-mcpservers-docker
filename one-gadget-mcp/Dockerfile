# One-Gadget MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="One-Gadget MCP Server - Find one-shot RCE gadgets in libc."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="one-gadget-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies, including Ruby and binutils-multiarch for objdump
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    ruby \
    binutils-multiarch \
    && rm -rf /var/lib/apt/lists/*

# Install one_gadget directly via RubyGems
RUN gem install one_gadget

WORKDIR /app

# Copy requirements and install Python dependencies
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory and set ownership
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8276
# Explicitly tell the server where to find the one_gadget binary
ENV ONE_GADGET_BIN=/usr/local/bin/one_gadget

EXPOSE 8276

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]