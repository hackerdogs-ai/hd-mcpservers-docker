# AI-Infra-Guard MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

# Stage 1: Build Go binary from source
FROM golang:1.23-alpine AS builder

WORKDIR /build

RUN apk add --no-cache git ca-certificates

RUN git clone --depth 1 https://github.com/Tencent/AI-Infra-Guard.git .

RUN go mod download

RUN CGO_ENABLED=0 go build -ldflags="-s -w" -trimpath -buildvcs=false -o ai-infra-guard ./cmd/cli/main.go

# Stage 2: Python MCP server
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="AI-Infra-Guard MCP Server - AI infrastructure security scanning and assessment"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="ai-infra-guard-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Go binary and data directories from builder
COPY --from=builder /build/ai-infra-guard /opt/ai-infra-guard/ai-infra-guard
COPY --from=builder /build/data /opt/ai-infra-guard/data
COPY --from=builder /build/trpc_go.yaml /opt/ai-infra-guard/trpc_go.yaml

COPY <<'WRAPPER' /usr/local/bin/ai-infra-guard
#!/bin/bash
cd /opt/ai-infra-guard
exec ./ai-infra-guard "$@"
WRAPPER
RUN chmod +x /usr/local/bin/ai-infra-guard /opt/ai-infra-guard/ai-infra-guard

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory and set permissions
RUN mkdir -p /app/output /opt/ai-infra-guard/logs /opt/ai-infra-guard/db \
    && chown -R mcpuser:mcpuser /app /opt/ai-infra-guard/logs /opt/ai-infra-guard/db

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8294

EXPOSE 8294

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
