FROM golang:1.23 AS builder
RUN CGO_ENABLED=0 go install github.com/lanrat/certgraph@latest

FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="CertGraph MCP Server - certificate relationship graphs"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL maintainer="support@hackerdogs.ai"
LABEL mcp-server-scope="remote"
LABEL org.opencontainers.image.title="certgraph-mcp"

COPY --from=builder /go/bin/certgraph /usr/local/bin/certgraph

RUN groupadd -g 1000 mcpuser && useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends tini ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_server.py ./
RUN chown -R mcpuser:mcpuser /app

USER mcpuser
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8519
EXPOSE 8519
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
