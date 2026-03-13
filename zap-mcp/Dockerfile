# OWASP ZAP MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.title="zap-mcp"

# 1. Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# 2. Install System Dependencies & Java Runtime
# Added 'wget' as it's sometimes more stable than curl for large tars
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    wget \
    tar \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# 3. Install ZAP from the official source
WORKDIR /opt/zap
RUN wget -qO- https://github.com/zaproxy/zaproxy/releases/download/v2.16.0/ZAP_2.16.0_Linux.tar.gz \
    | tar -xz --strip-components=1 && \
    ln -s /opt/zap/zap.sh /usr/local/bin/zap.sh && \
    chown -R mcpuser:mcpuser /opt/zap

# 4. Install MCP Python dependencies
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# 5. Copy app and fix permissions
COPY mcp_server.py ./
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# 6. Configuration
ENV PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8231 \
    # Give Java a memory limit inside the container
    JAVA_OPTS="-Xmx512m" 
    
EXPOSE 8231

USER mcpuser
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
