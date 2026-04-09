FROM node:20-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3 libicu72 && rm -rf /var/lib/apt/lists/*
RUN npm install -g @azure/mcp supergateway 2>/dev/null || npm install -g supergateway
COPY mcp_http_proxy.py /mcp_http_proxy.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8627
EXPOSE 8627
ENTRYPOINT ["/entrypoint.sh"]
