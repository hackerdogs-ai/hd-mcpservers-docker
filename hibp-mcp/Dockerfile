FROM node:20-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
RUN npm install -g @darrenjrobinson/hibp-mcp supergateway 2>/dev/null || npm install -g supergateway
COPY mcp_http_proxy.py /mcp_http_proxy.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV HIBP_API_KEY=dummy-hibp-api-key-for-mcp-list-tools-only
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8646
EXPOSE 8646
ENTRYPOINT ["/entrypoint.sh"]
