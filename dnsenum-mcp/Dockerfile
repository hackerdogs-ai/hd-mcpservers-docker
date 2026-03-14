# dnsenum MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="dnsenum MCP Server - DNS enumeration tool for discovering host information"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="dnsenum-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies AND the required Perl network/XML modules
# FIX: Added libxml-writer-perl to prevent the XML::Writer compile-time crash!
RUN apt-get update && apt-get install -y --no-install-recommends \
    perl \
    libnet-dns-perl \
    libnet-ip-perl \
    libnet-netmask-perl \
    libxml-libxml-perl \
    libxml-writer-perl \
    libstring-random-perl \
    git \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Cleanly clone the repository, make the Perl script executable, and symlink it
RUN git clone --depth 1 https://github.com/fwaeytens/dnsenum.git /opt/dnsenum && \
    chmod +x /opt/dnsenum/dnsenum.pl && \
    ln -sf /opt/dnsenum/dnsenum.pl /usr/local/bin/dnsenum

WORKDIR /app

# Copy requirements and install Python dependencies for the MCP wrapper
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory and grant permissions
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app /opt/dnsenum

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8304
ENV DNSENUM_BIN=/usr/local/bin/dnsenum

EXPOSE 8304

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]