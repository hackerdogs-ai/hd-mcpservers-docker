FROM node:20-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install ca-certificates over default (HTTP) mirrors first, then prefer HTTPS for follow-up apt.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends python3; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install MCP server globally (do not hide failures — empty image breaks HTTP/stdio at runtime)
RUN npm install -g clinicaltrialsgov-mcp-server

COPY mcp_http_proxy.py /mcp_http_proxy.py
COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8632
ENV MCP_PROXY_REQUEST_TIMEOUT=7200
ENV MCP_PROXY_INIT_TIMEOUT=360
EXPOSE 8632
ENTRYPOINT ["/entrypoint.sh"]
