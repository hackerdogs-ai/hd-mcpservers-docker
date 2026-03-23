FROM node:20-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
RUN npm install -g @brightdata/mcp supergateway 2>/dev/null || npm install -g supergateway
COPY mcp_http_proxy.py /mcp_http_proxy.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV BRIGHTDATA_API_TOKEN=dummy-brightdata-token-for-mcp-list-tools-only
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8630
EXPOSE 8630
ENTRYPOINT ["/entrypoint.sh"]
