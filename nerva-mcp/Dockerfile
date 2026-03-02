# Nerva MCP Server - Hackerdogs Ready
# Multi-stage build: Go builder + Python runtime
# Multi-arch build for linux/amd64 and linux/arm64

# Stage 1: Build nerva from source
FROM golang:1.24-bookworm AS builder
RUN go install github.com/praetorian-inc/nerva/cmd/nerva@latest

# Stage 2: Python runtime with nerva binary
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Nerva MCP Server - Network service fingerprinting and identification"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"

RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /go/bin/nerva /usr/local/bin/nerva
RUN chmod +x /usr/local/bin/nerva

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server.py ./

RUN mkdir -p /app/workdir && chown -R mcpuser:mcpuser /app

USER mcpuser

ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8104
ENV PYTHONUNBUFFERED=1

EXPOSE 8104

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
