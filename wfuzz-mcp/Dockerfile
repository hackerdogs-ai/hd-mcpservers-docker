# Wfuzz MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.title="wfuzz-mcp"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libcurl4-openssl-dev \
    ca-certificates \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 mcpuser \
 && useradd -m -u 1000 -g mcpuser -s /bin/bash mcpuser

# Fix pip compatibility
RUN pip install --no-cache-dir "pip<24.1"

# Install wfuzz + ensure pkg_resources exists
RUN pip install --no-cache-dir wfuzz setuptools wheel

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server.py ./

# Create output directory
RUN mkdir -p /app/output && chown -R 1000:1000 /app

USER 1000:1000

ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8224

EXPOSE 8224

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["python", "mcp_server.py"]

# Start MCP server
CMD ["python", "mcp_server.py"]
