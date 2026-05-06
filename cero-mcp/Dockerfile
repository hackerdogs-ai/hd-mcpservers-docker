# Cero MCP - Hackerdogs Ready
# Multi-stage: compile cero with a supported Go toolchain (Debian's golang-go is often too old for upstream).
FROM golang:1.22-bookworm AS cero-build
ENV CGO_ENABLED=0
RUN go install -trimpath -ldflags="-s -w" github.com/glebarez/cero@latest \
    && cp "$(go env GOPATH)/bin/cero" /cero.bin \
    && test -x /cero.bin

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Cero MCP - forgotten secrets in Git repos (cero CLI + FastMCP)"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL org.opencontainers.image.title="cero-mcp"

ENV DEBIAN_FRONTEND=noninteractive

RUN set -eux; \
    sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources; \
    APT_OPTS='-o Acquire::Retries=5 -o Acquire::http::Timeout=120 -o Acquire::https::Timeout=120'; \
    apt-get $APT_OPTS update; \
    apt-get $APT_OPTS install -y --no-install-recommends \
        ca-certificates \
        tini \
    ; \
    rm -rf /var/lib/apt/lists/*

COPY --from=cero-build /cero.bin /usr/local/bin/cero
RUN chmod 755 /usr/local/bin/cero && test -x /usr/local/bin/cero

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
ENV MCP_PORT=8396
ENV BIN=/usr/local/bin/cero
EXPOSE 8396

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
