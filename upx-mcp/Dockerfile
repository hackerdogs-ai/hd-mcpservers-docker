# UPX MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="UPX MCP Server - Executable packer/unpacker."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="upx-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies (wget and xz-utils are needed for the download/extraction)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    git \
    unzip \
    ca-certificates \
    wget \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Download and install the latest UPX directly from GitHub releases
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then UPX_ARCH="amd64"; elif [ "$ARCH" = "aarch64" ]; then UPX_ARCH="arm64"; else UPX_ARCH="amd64"; fi && \
    UPX_VERSION="4.2.4" && \
    wget -q "https://github.com/upx/upx/releases/download/v${UPX_VERSION}/upx-${UPX_VERSION}-${UPX_ARCH}_linux.tar.xz" && \
    tar -xJf "upx-${UPX_VERSION}-${UPX_ARCH}_linux.tar.xz" && \
    cp "upx-${UPX_VERSION}-${UPX_ARCH}_linux/upx" /usr/local/bin/upx && \
    chmod +x /usr/local/bin/upx && \
    rm -rf "upx-${UPX_VERSION}-${UPX_ARCH}_linux"* "upx-${UPX_VERSION}-${UPX_ARCH}_linux.tar.xz"

WORKDIR /app

# Copy requirements and install Python dependencies
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./
COPY hd_fetch.py ./

# Create output and temp directories
RUN mkdir -p /app/output /app/temp_workspace && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8284
# Explicitly tell the server where to find the manually installed binary
ENV UPX_BIN=/usr/local/bin/upx

EXPOSE 8284

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]