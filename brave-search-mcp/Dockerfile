FROM node:20-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
RUN npm install -g @modelcontextprotocol/server-brave-search supergateway 2>/dev/null || npm install -g supergateway
COPY mcp_http_proxy.py /mcp_http_proxy.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV BRAVE_API_KEY=dummy-brave-api-key-for-mcp-list-tools-only-not-valid
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8629
EXPOSE 8629
ENTRYPOINT ["/entrypoint.sh"]
