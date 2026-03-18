# Assetfinder MCP - Hackerdogs Ready
FROM python:3.12-slim-bookworm
RUN groupadd -g 1000 mcpuser && useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser
RUN apt-get update && apt-get install -y --no-install-recommends golang-go ca-certificates && rm -rf /var/lib/apt/lists/*
ENV GOPATH=/go PATH="/go/bin:$PATH"
RUN go install github.com/tomnomnom/assetfinder@latest
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_server.py ./
RUN chown -R mcpuser:mcpuser /app
USER mcpuser
ENV PYTHONUNBUFFERED=1 MCP_TRANSPORT=stdio MCP_PORT=8384
EXPOSE 8384
CMD ["python", "mcp_server.py"]
