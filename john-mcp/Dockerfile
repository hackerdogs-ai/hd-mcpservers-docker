# John the Ripper (Jumbo) MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="John the Ripper MCP Server - Password hash cracking with custom rules."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="john-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install build dependencies for JtR Jumbo
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    yasm \
    pkg-config \
    tini \
    git \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Clone and compile the bleeding-jumbo branch from Openwall
RUN git clone --depth 1 -b bleeding-jumbo https://github.com/openwall/john.git /opt/john && \
    cd /opt/john/src && \
    ./configure && \
    make -s clean && \
    make -sj4 && \
    chown -R mcpuser:mcpuser /opt/john

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./
COPY hd_fetch.py ./

# Create output directory and grant permissions
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8234
# The compiled Jumbo binary lives here
ENV JOHN_BIN=/opt/john/run/john

EXPOSE 8234

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]