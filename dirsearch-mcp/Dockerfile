# Dirsearch MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Dirsearch MCP Server - Directory and file discovery."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="dirsearch-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Install minimal dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 mcpuser \
    && useradd -m -u 1000 -g mcpuser -s /bin/bash mcpuser

# Install dirsearch
RUN git clone https://github.com/maurosoria/dirsearch.git /opt/dirsearch \
    && pip install --no-cache-dir -r /opt/dirsearch/requirements.txt

# Create CLI wrapper
RUN ln -s /opt/dirsearch/dirsearch.py /usr/local/bin/dirsearch \
    && chmod +x /opt/dirsearch/dirsearch.py

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY mcp_server.py ./

# Create output directory and assign ownership
RUN mkdir -p /app/output \
    && chown -R mcpuser:mcpuser /app /opt/dirsearch

USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8215
ENV DIRSEARCH_PATH=/opt/dirsearch

EXPOSE 8215

# Proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
