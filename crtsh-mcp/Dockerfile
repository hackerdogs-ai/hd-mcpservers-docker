# crt.sh MCP Server - Hackerdogs Ready
# API-only; stdio + streamable-http via FastMCP
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="crt.sh MCP Server - subdomain discovery from certificate logs"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL maintainer="support@hackerdogs.ai"
LABEL org.opencontainers.image.title="crtsh-mcp"

ENV DEBIAN_FRONTEND=noninteractive

# OS deps before app user; HTTPS mirrors + retries reduce flaky apt/pip TLS during build.
RUN set -eux; \
    sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources; \
    APT_OPTS='-o Acquire::Retries=5 -o Acquire::http::Timeout=120 -o Acquire::https::Timeout=120'; \
    apt-get $APT_OPTS update; \
    apt-get $APT_OPTS install -y --no-install-recommends \
        ca-certificates \
        tini \
    ; \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 mcpuser && useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY mcp_server.py ./
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

USER mcpuser
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8381
EXPOSE 8381

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
