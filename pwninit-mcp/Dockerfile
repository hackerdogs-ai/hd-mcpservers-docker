# Pwninit MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

# Stage 1: Builder for the Rust binary
FROM rust:slim-bookworm AS builder
# Install build dependencies required for compiling xz2 and openssl crates
RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    liblzma-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pwninit directly via cargo
RUN cargo install pwninit

# Stage 2: Final lightweight Python environment
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Pwninit MCP Server - Automate binary exploitation setup."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="pwninit-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies
# patchelf and elfutils are strictly required for pwninit to modify binary linkings
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    patchelf \
    elfutils \
    liblzma5 \
    libssl3 \
    file \
    && rm -rf /var/lib/apt/lists/*

# Copy the compiled binary from the Rust builder stage
COPY --from=builder /usr/local/cargo/bin/pwninit /usr/local/bin/pwninit

WORKDIR /app

# Copy requirements and install Python dependencies
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory and set ownership
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8278
# Explicitly tell the server where to find the pwninit binary
ENV PWNINIT_BIN=/usr/local/bin/pwninit

EXPOSE 8278

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]