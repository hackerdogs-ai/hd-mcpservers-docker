# Wafw00f MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Wafw00f MCP Server - Web application firewall fingerprinting."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL org.opencontainers.image.title="wafw00f-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.authors="hackerdogs"
LABEL maintainer="support@hackerdogs.ai"
LABEL mcp-server-scope="remote"

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install minimal system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        tini \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir wafw00f

# Copy application
COPY mcp_server.py .

# Create output directory
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root
USER mcpuser

ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8230

EXPOSE 8230

# Proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["python", "mcp_server.py"]
