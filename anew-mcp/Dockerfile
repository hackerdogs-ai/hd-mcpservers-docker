# Anew MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

# -------- Build anew --------
FROM golang:1.24-bookworm AS builder

RUN go install github.com/tomnomnom/anew@latest


# -------- Runtime --------
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Anew MCP Server - Append new lines for efficient data processing."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="anew-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Runtime utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy anew binary
COPY --from=builder /go/bin/anew /usr/local/bin/anew

WORKDIR /app

# Python dependencies for MCP server
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# MCP server
COPY mcp_server.py ./

# Output directory
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

USER mcpuser

ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8229

EXPOSE 8229

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["python", "mcp_server.py"]
