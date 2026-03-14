# GDB-PEDA MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="GDB-PEDA MCP Server - GNU Debugger with PEDA (exploit development)."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="peda-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install GDB, Git (to download PEDA), file, and binutils
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdb \
    git \
    file \
    binutils \
    procps \
    tini \
    git \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Clone PEDA and inject it into .gdbinit for the mcpuser
# FIX: PEDA has a hardcoded color output setting in its lib/config.py. We use sed to switch it to 'off' so the LLM can read the text!
RUN git clone https://github.com/longld/peda.git /home/mcpuser/peda && \
    echo "source /home/mcpuser/peda/peda.py" > /home/mcpuser/.gdbinit && \
    sed -i "s/'color'       : ('on',/'color'       : ('off',/g" /home/mcpuser/peda/lib/config.py && \
    chown -R mcpuser:mcpuser /home/mcpuser

WORKDIR /app

# Copy requirements and install Python dependencies for the wrapper
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./
COPY hd_fetch.py ./

# Create output directory and grant permissions
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8237
# native gdb binary path
ENV PEDA_BIN=/usr/bin/gdb

EXPOSE 8237

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]