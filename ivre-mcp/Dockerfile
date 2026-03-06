# IVRE MCP Server - Hackerdogs Ready
# Single-stage build: Python HTTP client for IVRE Web API
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="IVRE MCP Server - Network reconnaissance query interface via IVRE Web API"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"

LABEL org.opencontainers.image.title="ivre-mcp"
LABEL org.opencontainers.image.licenses="GPL-3.0"
LABEL org.opencontainers.image.author="hackerdogs"

RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server.py ./

RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

USER mcpuser

ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8366
ENV IVRE_WEB_URL=""
ENV IVRE_VERIFY_SSL=true

EXPOSE 8366

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["python", "mcp_server.py"]
