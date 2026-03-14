# Tplmap MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64
# Uses Python 3.12; tplmap's requirements install excludes wsgiref (Python 2-only, built-in to Py3).

# Downgraded to 3.10 to ensure legacy module support (like cgi/telnetlib)
FROM python:3.10-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Tplmap MCP Server - Server-side template injection exploitation."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="tplmap-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies, including git to clone the repository
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone the Tplmap repository directly from GitHub and link it
RUN git clone --depth 1 https://github.com/epinna/tplmap.git /opt/tplmap && \
    chmod +x /opt/tplmap/tplmap.py && \
    ln -s /opt/tplmap/tplmap.py /usr/local/bin/tplmap

WORKDIR /app

# Copy requirements and install Python dependencies
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Strip strict version pins AND completely remove the obsolete 'wsgiref' Python 2 package
RUN sed -e 's/==.*//' -e '/wsgiref/d' /opt/tplmap/requirements.txt > /opt/tplmap/requirements_unpinned.txt && \
    pip install --no-cache-dir -r /opt/tplmap/requirements_unpinned.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory and grant permissions
RUN mkdir -p /app/output && \
    chown -R mcpuser:mcpuser /app /opt/tplmap

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8267
# Suppress Python warnings to prevent MCP stdio corruption
ENV PYTHONWARNINGS="ignore::DeprecationWarning"
# Explicitly tell the server where to find the tplmap binary
ENV TPLMAP_BIN=/usr/local/bin/tplmap

EXPOSE 8267

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]