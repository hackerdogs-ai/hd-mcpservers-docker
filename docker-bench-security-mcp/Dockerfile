# Docker Bench Security MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Docker Bench Security MCP Server - Docker security assessment (CIS)."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="docker-bench-security-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

COPY --from=docker:27-cli /usr/local/bin/docker /usr/local/bin/docker

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    git \
    unzip \
    ca-certificates \
    procps \
    iproute2 \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/docker/docker-bench-security.git /opt/docker-bench-security \
    && chmod +x /opt/docker-bench-security/docker-bench-security.sh \
    && mkdir -p /opt/docker-bench-security/log \
    && chown -R 1000:1000 /opt/docker-bench-security/log

COPY <<'WRAPPER' /usr/local/bin/docker-bench-security.sh
#!/bin/bash
cd /opt/docker-bench-security
exec ./docker-bench-security.sh "$@"
WRAPPER
RUN chmod +x /usr/local/bin/docker-bench-security.sh

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
ENV MCP_PORT=8254

EXPOSE 8254

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
