FROM node:20-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
# Text2Go upstream: https://github.com/Text2Go/ai-humanizer-mcp-server — npm per their README (`npx -y ai-humanizer-mcp-server`)
RUN npm install -g ai-humanizer-mcp-server supergateway
COPY mcp_http_proxy.py /mcp_http_proxy.py
COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8601
EXPOSE 8601
ENTRYPOINT ["/entrypoint.sh"]
