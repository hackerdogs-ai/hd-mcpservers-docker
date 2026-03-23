# Feroxbuster MCP Server - Hackerdogs Ready
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.title="feroxbuster-mcp"

# 1. Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# 2. Install System Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 3. Install Feroxbuster (Multi-arch binary download)
RUN arch=$(dpkg --print-architecture) && \
    if [ "$arch" = "amd64" ]; then \
        FEROX_URL="https://github.com/epi052/feroxbuster/releases/latest/download/x86_64-linux-feroxbuster.zip"; \
    elif [ "$arch" = "arm64" ]; then \
        FEROX_URL="https://github.com/epi052/feroxbuster/releases/latest/download/aarch64-linux-feroxbuster.zip"; \
    fi && \
    curl -sL "$FEROX_URL" -o feroxbuster.zip && \
    unzip feroxbuster.zip && \
    mv feroxbuster /usr/local/bin/ && \
    chmod +x /usr/local/bin/feroxbuster && \
    rm feroxbuster.zip

WORKDIR /app

# 4. Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy app and fix permissions (AS ROOT)
COPY hd_fetch.py ./
COPY mcp_server.py ./
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# 6. Configuration
ENV PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8216
EXPOSE 8216

# 7. Drop privileges
USER mcpuser

# 8. Execution
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
