# HashPump MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

# Stage 1: Builder for the C++ binary
FROM python:3.12-slim-bookworm AS builder
# Install C++ compilers, make, and OpenSSL development headers
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    g++ \
    make \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# The original bwall repo is offline, so we use a stable, maintained community fork
RUN git clone --depth 1 https://github.com/mheistermann/HashPump-partialhash.git /opt/HashPump
WORKDIR /opt/HashPump
RUN make

# Stage 2: Final lightweight Python environment
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="HashPump MCP Server - Hash length extension attacks."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="hashpump-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies (including libssl3 for HashPump's dynamic linking)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    git \
    unzip \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Copy the compiled binary from the builder stage (using the correct lowercase name!)
COPY --from=builder /opt/HashPump/hashpump /usr/local/bin/hashpump
RUN chmod +x /usr/local/bin/hashpump

WORKDIR /app

# Copy requirements and install Python dependencies
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./
COPY hd_fetch.py ./

# Create output directory and adjust permissions
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8274
# Explicitly tell the server where to find the hashpump binary
ENV HASHPUMP_BIN=/usr/local/bin/hashpump

EXPOSE 8274

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]