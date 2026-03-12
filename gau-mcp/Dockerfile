# --- Stage 1: Build GAU ---
FROM golang:1.24-bookworm AS builder
# Installing the latest version of GAU (v2)
RUN go install github.com/lc/gau/v2/cmd/gau@latest

# --- Stage 2: Final MCP Server ---
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="GAU MCP Server - Get All URLs (Wayback, Common Crawl, etc.)."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="gau-mcp"
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

# 3. Copy GAU binary from the builder stage
COPY --from=builder /go/bin/gau /usr/local/bin/gau

WORKDIR /app

# 4. Install MCP Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy application code and fix permissions (AS ROOT)
COPY mcp_server.py ./
RUN mkdir -p /app/output && \
    chown -R mcpuser:mcpuser /app && \
    chmod +x /usr/local/bin/gau

# 6. Environment & Networking
ENV PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8218
EXPOSE 8218

# 7. Drop privileges
USER mcpuser

# 8. Execution
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
