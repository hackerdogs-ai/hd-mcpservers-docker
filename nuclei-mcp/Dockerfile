# Nuclei MCP - Hackerdogs Ready (nuclei v3 requires Go >= 1.24.2)
FROM golang:1.25-bookworm AS builder
RUN go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

FROM python:3.12-slim-bookworm
RUN groupadd -g 1000 mcpuser && useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /go/bin/nuclei /usr/local/bin/nuclei
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_server.py ./
RUN chown -R mcpuser:mcpuser /app
USER mcpuser
ENV PYTHONUNBUFFERED=1 MCP_TRANSPORT=stdio MCP_PORT=8391
EXPOSE 8391
CMD ["python", "mcp_server.py"]
