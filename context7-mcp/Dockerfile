FROM node:20-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
RUN npm install -g @upstash/context7-mcp supergateway 2>/dev/null || npm install -g supergateway
COPY mcp_http_proxy.py /mcp_http_proxy.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8634
EXPOSE 8634
ENTRYPOINT ["/entrypoint.sh"]
