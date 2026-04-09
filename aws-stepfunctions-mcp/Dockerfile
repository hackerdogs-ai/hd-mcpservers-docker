FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir fastmcp uvicorn httpx boto3
COPY mcp_server.py .
COPY mcp_http_proxy.py /mcp_http_proxy.py
COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8625
EXPOSE 8625
ENTRYPOINT ["/entrypoint.sh"]
