FROM node:20-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends python3; \
    rm -rf /var/lib/apt/lists/*

RUN npm install -g @cloudflare/mcp-server-cloudflare

COPY mcp_http_proxy.py /mcp_http_proxy.py
COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENV CLOUDFLARE_API_TOKEN=dummy-cf-api-token-for-mcp-list-tools-only
ENV CLOUDFLARE_ACCOUNT_ID=00000000000000000000000000000000
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8633
EXPOSE 8633
ENTRYPOINT ["/entrypoint.sh"]
