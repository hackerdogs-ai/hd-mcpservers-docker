# AWS Network MCP — awslabs.aws-network-mcp-server (stdio + Python HTTP proxy for streamable-http)
# Node/supergateway multi-stage removed: entrypoint uses mcp_http_proxy.py only (same runtime path as stdio).

FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="AWS Network MCP Server — Cloud WAN, TGW, VPC, Network Firewall, VPN (read-only)"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL org.opencontainers.image.title="aws-network-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    tini \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "awslabs.aws-network-mcp-server>=0.0.9"

COPY mcp_http_proxy.py /mcp_http_proxy.py
COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8618
EXPOSE 8618

ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
