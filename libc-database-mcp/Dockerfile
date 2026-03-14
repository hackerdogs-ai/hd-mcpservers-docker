# Libc-Database MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Libc-Database MCP Server - Libc identification and offset lookup (use find script)."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="libc-database-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    git \
    unzip \
    ca-certificates \
    binutils \
    file \
    perl \
    wget \
    tar \
    zstd \
    jq \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/niklasb/libc-database.git /opt/libc-database \
    && chmod +x /opt/libc-database/find /opt/libc-database/dump /opt/libc-database/identify \
       /opt/libc-database/download /opt/libc-database/get /opt/libc-database/add 2>/dev/null || true \
    && mkdir -p /opt/libc-database/db /opt/libc-database/libs \
    && chown -R 1000:1000 /opt/libc-database/db /opt/libc-database/libs

COPY <<'WRAPPER' /usr/local/bin/libc-find
#!/bin/bash
cd /opt/libc-database
exec ./find "$@"
WRAPPER

COPY <<'WRAPPER' /usr/local/bin/libc-dump
#!/bin/bash
cd /opt/libc-database
exec ./dump "$@"
WRAPPER

COPY <<'WRAPPER' /usr/local/bin/libc-identify
#!/bin/bash
cd /opt/libc-database
exec ./identify "$@"
WRAPPER

COPY <<'WRAPPER' /usr/local/bin/libc-download
#!/bin/bash
cd /opt/libc-database
exec ./download "$@"
WRAPPER

COPY <<'WRAPPER' /usr/local/bin/libc-get
#!/bin/bash
cd /opt/libc-database
exec ./get "$@"
WRAPPER

RUN chmod +x /usr/local/bin/libc-find /usr/local/bin/libc-dump \
    /usr/local/bin/libc-identify /usr/local/bin/libc-download /usr/local/bin/libc-get

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./
COPY hd_fetch.py ./

# Create output directory
RUN mkdir -p /app/output /app/workdir && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8277
ENV LIBC_DATABASE_BIN=libc-find

EXPOSE 8277

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
