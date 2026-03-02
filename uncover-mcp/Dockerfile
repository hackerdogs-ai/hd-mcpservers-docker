# Uncover MCP Server - Hackerdogs Ready
# Multi-stage build: Go binary + Python MCP server
# Multi-arch build for linux/amd64 and linux/arm64

# Stage 1: Build uncover from source
FROM golang:1.24-bookworm AS builder

RUN go install -v github.com/projectdiscovery/uncover/cmd/uncover@latest

# Stage 2: Runtime with Python MCP server
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Uncover MCP Server - Exposed host discovery via search APIs"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"

LABEL org.opencontainers.image.title="uncover-mcp"
LABEL org.opencontainers.image.licenses="MIT License"
LABEL org.opencontainers.image.author="hackerdogs"

RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /go/bin/uncover /usr/local/bin/uncover

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server.py ./

RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

USER mcpuser

ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8107

EXPOSE 8107

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["python", "mcp_server.py"]
