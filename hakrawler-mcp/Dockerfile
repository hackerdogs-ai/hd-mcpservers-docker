# Hakrawler MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

# --- Stage 1: Build Hakrawler ---
FROM golang:1.24-bookworm AS builder
RUN go install github.com/hakluke/hakrawler@latest

# --- Stage 2: Final MCP Server ---
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Hakrawler MCP Server - Fast web endpoint discovery and crawling."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="hakrawler-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# 1. Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# 2. Install System Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 3. Copy Hakrawler binary from the builder stage
COPY --from=builder /go/bin/hakrawler /usr/local/bin/hakrawler

WORKDIR /app

# 4. Install MCP Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy application code and fix permissions (AS ROOT)
COPY mcp_server.py ./
RUN mkdir -p /app/output && \
    chown -R mcpuser:mcpuser /app && \
    chmod +x /usr/local/bin/hakrawler

# 6. Environment & Networking
ENV PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8217
EXPOSE 8217

# 7. Drop privileges
USER mcpuser

# 8. Execution
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
