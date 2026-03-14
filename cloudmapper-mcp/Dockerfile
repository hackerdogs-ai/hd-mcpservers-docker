# CloudMapper MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="CloudMapper MCP Server - AWS network visualization and security."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="cloudmapper-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    git \
    ca-certificates \
    build-essential \
    autoconf \
    automake \
    libtool \
    jq \
    libjq-dev \
    libonig-dev \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/duo-labs/cloudmapper.git /opt/cloudmapper \
    && pip install --no-cache-dir \
        boto3 botocore jinja2 netaddr pyyaml requests \
        pyjq policyuniverse parliament \
        json-cfg kwonly-args six \
    && chown -R 1000:1000 /opt/cloudmapper

COPY <<'WRAPPER' /usr/local/bin/cloudmapper
#!/bin/bash
cd /opt/cloudmapper
exec python cloudmapper.py "$@"
WRAPPER
RUN chmod +x /usr/local/bin/cloudmapper

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
ENV MCP_PORT=8268

EXPOSE 8268

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
