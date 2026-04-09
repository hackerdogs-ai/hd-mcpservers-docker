# Shuffledns MCP - Hackerdogs Ready (shuffledns requires Go >= 1.24.0)
FROM golang:1.25-bookworm AS builder
RUN go install github.com/projectdiscovery/shuffledns/cmd/shuffledns@latest

FROM python:3.12-slim-bookworm
RUN groupadd -g 1000 mcpuser && useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /go/bin/shuffledns /usr/local/bin/shuffledns
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_server.py ./
RUN chown -R mcpuser:mcpuser /app
USER mcpuser
ENV PYTHONUNBUFFERED=1 MCP_TRANSPORT=stdio MCP_PORT=8393
EXPOSE 8393
CMD ["python", "mcp_server.py"]
