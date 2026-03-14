# Nikto MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL org.opencontainers.image.title="nikto-mcp"

# 1. Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# 2. Install Perl and required modules
RUN apt-get update && apt-get install -y --no-install-recommends \
    perl \
    libnet-ssleay-perl \
    libjson-perl \
    libxml-writer-perl \
    liblwp-protocol-https-perl \
    tini \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# 3. Install Nikto from Source
WORKDIR /opt
RUN git clone --depth=1 https://github.com/sullo/nikto.git && \
    ln -s /opt/nikto/program/nikto.pl /usr/local/bin/nikto && \
    chown -R mcpuser:mcpuser /opt/nikto

WORKDIR /app

# 4. Install MCP Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy app and fix permissions
COPY mcp_server.py ./
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# 6. Configuration
ENV PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8219
EXPOSE 8219

USER mcpuser

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
