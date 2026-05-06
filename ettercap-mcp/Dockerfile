# Ettercap MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Ettercap MCP Server - Comprehensive suite for man-in-the-middle attacks on LAN"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="ettercap-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

ENV DEBIAN_FRONTEND=noninteractive

# Install OS packages before creating the app user (avoids dpkg/postinst edge cases with UID 1000).
# Use HTTPS for Debian (python slim defaults to http); reduces flaky CDN / proxy "connection closed" on large .deb fetches.
# Apt retries/timeouts further reduce exit-code-100 failures on slow mirrors.
RUN set -eux; \
    sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources; \
    APT_OPTS='-o Acquire::Retries=5 -o Acquire::http::Timeout=120 -o Acquire::https::Timeout=120'; \
    apt-get $APT_OPTS update; \
    apt-get $APT_OPTS install -y --no-install-recommends \
        ca-certificates \
        tini \
        ettercap-common \
        ettercap-text-only \
    ; \
    rm -rf /var/lib/apt/lists/*

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8313

EXPOSE 8313

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
