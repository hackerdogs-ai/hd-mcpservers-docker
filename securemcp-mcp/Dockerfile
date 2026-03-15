# SecureMCP MCP Server - Hackerdogs Ready
# Single builder stage: build SecureMCP binary, then Python runtime with binary in PATH.

# ---- Stage 1: Build SecureMCP from source ----
FROM golang:1.23-bookworm AS builder
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV CGO_ENABLED=0 GOOS=linux
WORKDIR /opt/securemcp
RUN git clone --depth 1 https://github.com/makalin/SecureMCP.git . \
    && sed -i '/\/\/ TODO: Implement response body analysis/i _ = vulnerabilityIndicators' internal/scanner/prompt.go \
    && go mod download \
    && go mod tidy \
    && go build -mod=mod -ldflags="-s -w" -o bin/securemcp ./cmd/securemcp/main.go \
    && test -f bin/securemcp

# ---- Stage 2: Runtime with Python MCP server ----
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="SecureMCP MCP Server - MCP server security hardening and validation tool"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="securemcp-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy binary from builder (path must match where builder wrote it)
COPY --from=builder /opt/securemcp/bin/securemcp /usr/local/bin/securemcp
RUN chmod +x /usr/local/bin/securemcp

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server.py ./

RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

USER mcpuser

ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8297
# Binary is in /usr/local/bin (on default PATH); set explicitly so server finds it
ENV SECUREMCP_BIN=/usr/local/bin/securemcp

EXPOSE 8297

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
