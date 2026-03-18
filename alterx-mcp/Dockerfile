# Alterx MCP Server - Hackerdogs Ready
# stdio + streamable-http via FastMCP only
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Alterx MCP Server - pattern-based wordlist for subdomain discovery"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL maintainer="support@hackerdogs.ai"
LABEL org.opencontainers.image.title="alterx-mcp"

RUN groupadd -g 1000 mcpuser && useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    tini \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install alterx binary (projectdiscovery/alterx)
ARG ALTERX_VERSION=0.1.0
ARG TARGETARCH
RUN case "${TARGETARCH}" in \
    amd64) ARCH=linux_amd64 ;; \
    arm64) ARCH=linux_arm64 ;; \
    *) ARCH=linux_amd64 ;; esac \
    && wget -q "https://github.com/projectdiscovery/alterx/releases/download/v${ALTERX_VERSION}/alterx_${ALTERX_VERSION}_${ARCH}.zip" -O /tmp/alterx.zip \
    && unzip -q /tmp/alterx.zip -d /usr/local/bin \
    && chmod +x /usr/local/bin/alterx \
    && rm /tmp/alterx.zip

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_server.py ./
RUN chown -R mcpuser:mcpuser /app

USER mcpuser
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8380
EXPOSE 8380

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
