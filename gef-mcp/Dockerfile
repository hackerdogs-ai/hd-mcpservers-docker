# GDB-GEF MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="GDB-GEF MCP Server - GDB Enhanced Features for exploit development."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="gef-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install GDB, wget (to download GEF), file, binutils, and procps (required by GEF init)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdb \
    wget \
    file \
    binutils \
    procps \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install GEF for the mcpuser
# FIX: Bypass the flaky shortlink and pull directly from the raw GitHub repo!
RUN wget -O /home/mcpuser/.gdbinit-gef.py -q https://raw.githubusercontent.com/hugsy/gef/main/gef.py && \
    echo "source /home/mcpuser/.gdbinit-gef.py" > /home/mcpuser/.gdbinit && \
    echo "gef config gef.disable_color True" >> /home/mcpuser/.gdbinit && \
    chown -R mcpuser:mcpuser /home/mcpuser

WORKDIR /app

# Copy requirements and install Python dependencies for the wrapper
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory and grant permissions
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8238
# native gdb binary path
ENV GEF_BIN=/usr/bin/gdb

EXPOSE 8238

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]