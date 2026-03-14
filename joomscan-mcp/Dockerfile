# JoomScan MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="JoomScan MCP Server - OWASP Joomla vulnerability scanner"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="joomscan-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies AND the required Perl network/regex modules
RUN apt-get update && apt-get install -y --no-install-recommends \
    perl \
    libwww-perl \
    liblwp-protocol-https-perl \
    libregexp-common-perl \
    libnet-dns-perl \
    libxml-libxml-perl \
    git \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Cleanly clone the repository and make the Perl script executable
RUN git clone --depth 1 https://github.com/OWASP/joomscan.git /opt/joomscan && \
    chmod +x /opt/joomscan/joomscan.pl && \
    ln -sf /opt/joomscan/joomscan.pl /usr/local/bin/joomscan

# FIX 1: Prevent JoomScan from hanging for 3 minutes on its HTTP update check!
RUN sed -i 's/&check_update;//g' /opt/joomscan/joomscan.pl || true

WORKDIR /app

# Copy requirements and install Python dependencies for the wrapper
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# FIX 2: Symlink the hardcoded reports folder directly to your mapped volume
RUN mkdir -p /app/output && \
    rm -rf /opt/joomscan/reports && \
    ln -s /app/output /opt/joomscan/reports && \
    chown -R mcpuser:mcpuser /app /opt/joomscan

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8305
ENV JOOMSCAN_BIN=/opt/joomscan/joomscan.pl

EXPOSE 8305

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]