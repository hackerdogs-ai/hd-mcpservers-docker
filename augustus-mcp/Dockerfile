# Augustus MCP Server - Hackerdogs Ready
# Multi-stage build: Go builder + Python runtime
# Multi-arch build for linux/amd64 and linux/arm64

# ---- Stage 1: Build augustus from source ----
FROM golang:1.25-bookworm AS builder

RUN go install github.com/praetorian-inc/augustus/cmd/augustus@latest

# ---- Stage 2: Runtime ----
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Augustus MCP Server - LLM adversarial vulnerability testing"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="augustus-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy augustus binary from builder
COPY --from=builder /go/bin/augustus /usr/local/bin/augustus

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8101

EXPOSE 8101

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
