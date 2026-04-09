FROM node:20-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
RUN npm install -g @programcomputer/nasa-mcp-server supergateway 2>/dev/null || npm install -g supergateway
COPY mcp_http_proxy.py /mcp_http_proxy.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV NASA_API_KEY=DEMO_KEY
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8651
EXPOSE 8651
ENTRYPOINT ["/entrypoint.sh"]
