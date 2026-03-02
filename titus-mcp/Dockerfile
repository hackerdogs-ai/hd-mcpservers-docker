# Titus MCP Server - Hackerdogs Ready
# Multi-stage build: Go builder + Python runtime
# Multi-arch build for linux/amd64 and linux/arm64

# Stage 1: Build titus from source
FROM golang:1.25-bookworm AS builder
RUN apt-get update && apt-get install -y make git libhyperscan-dev pkg-config
RUN git clone https://github.com/praetorian-inc/titus.git /titus
WORKDIR /titus
RUN make build

# Stage 2: Python runtime with titus binary
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Titus MCP Server - Secret detection in source code and git history"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"

RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /titus/dist/titus /usr/local/bin/titus
RUN chmod +x /usr/local/bin/titus

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server.py ./

RUN mkdir -p /app/workdir && chown -R mcpuser:mcpuser /app

USER mcpuser

ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8103
ENV PYTHONUNBUFFERED=1

EXPOSE 8103

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
