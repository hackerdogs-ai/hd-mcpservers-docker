# Blackbird MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Blackbird MCP Server - Username OSINT search across 500+ sites."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="blackbird-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone Blackbird and install dependencies
RUN git clone --depth 1 https://github.com/p1ngul1n0/blackbird.git /opt/blackbird && \
    pip install --no-cache-dir -r /opt/blackbird/requirements.txt

# Create wrapper script
COPY <<'WRAPPER' /usr/local/bin/blackbird
#!/bin/bash
cd /opt/blackbird
exec python blackbird.py "$@"
WRAPPER
RUN chmod +x /usr/local/bin/blackbird

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server.py ./

RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app /opt/blackbird

USER mcpuser

ENV BLACKBIRD_BIN=blackbird
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8220

EXPOSE 8220

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
