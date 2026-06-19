# Patator MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Patator MCP Server - Multi-purpose brute-forcer."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="patator-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Patator pulls python3-impacket from Debian; apt CDN often flakes on that single .deb — prefetch with curl, then apt.
RUN printf 'Acquire::Retries "8";\nAcquire::http::Timeout "120";\nAcquire::https::Timeout "120";\n' > /etc/apt/apt.conf.d/99retries
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl; \
    for i in 1 2 3 4 5 6 7 8 9 10; do \
      if curl -fsSL --retry 25 --retry-delay 5 --retry-all-errors \
        -o /tmp/python3-impacket.deb \
        "https://deb.debian.org/debian/pool/main/i/impacket/python3-impacket_0.10.0-4_all.deb"; then \
        break; \
      fi; \
      echo "curl impacket attempt $i failed"; sleep 20; \
    done; \
    test -s /tmp/python3-impacket.deb; \
    dpkg -i /tmp/python3-impacket.deb || true; \
    apt-get install -y --no-install-recommends -f; \
    apt-get install -y --no-install-recommends tini patator; \
    apt-get purge -y curl; \
    apt-get autoremove -y; \
    rm -f /tmp/python3-impacket.deb; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
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
ENV MCP_PORT=8262
# Explicitly tell the server where to find the patator binary
ENV PATATOR_BIN=/usr/bin/patator
# Suppress Python warnings (like telnetlib deprecation) to prevent MCP stdio corruption
ENV PYTHONWARNINGS="ignore::DeprecationWarning"

EXPOSE 8262

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]