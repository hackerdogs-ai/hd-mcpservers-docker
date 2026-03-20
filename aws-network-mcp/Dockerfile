FROM node:20-slim AS supergateway-builder
RUN npm install -g supergateway && npm cache clean --force

FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN pip install --no-cache-dir awslabs.aws-network-mcp-server

# Add Node.js + supergateway for HTTP mode
COPY --from=supergateway-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=supergateway-builder /usr/local/lib/node_modules/supergateway /usr/local/lib/node_modules/supergateway

COPY mcp_http_proxy.py /mcp_http_proxy.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8618
EXPOSE 8618
ENTRYPOINT ["/entrypoint.sh"]
