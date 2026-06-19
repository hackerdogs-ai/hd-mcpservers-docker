FROM node:20-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
RUN npm install -g @cenemiljezweb/dns-mcp-server supergateway 2>/dev/null || npm install -g supergateway
COPY mcp_http_proxy.py /mcp_http_proxy.py
COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8635
EXPOSE 8635
ENTRYPOINT ["/entrypoint.sh"]
