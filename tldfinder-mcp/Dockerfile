# TLDFinder MCP Server - Hackerdogs Ready
# Multi-stage build: Go binary + Python MCP server
# Multi-arch build for linux/amd64 and linux/arm64

# Stage 1: Build tldfinder from source
FROM golang:1.24-bookworm AS builder

RUN go install github.com/projectdiscovery/tldfinder/cmd/tldfinder@latest

# Stage 2: Runtime with Python MCP server
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="TLDFinder MCP Server - TLD and subdomain discovery via passive and active DNS"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"

LABEL org.opencontainers.image.title="tldfinder-mcp"
LABEL org.opencontainers.image.licenses="MIT License"
LABEL org.opencontainers.image.author="hackerdogs"

RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /go/bin/tldfinder /usr/local/bin/tldfinder

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server.py ./

RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

USER mcpuser

ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8113

EXPOSE 8113

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["python", "mcp_server.py"]
