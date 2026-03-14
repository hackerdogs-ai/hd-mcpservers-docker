# ---- Stage 1: Build Ramparts from source via Cargo ----
# FIX: Use the rolling 'slim-bookworm' tag to always get the latest stable Rust compiler (1.89+)
FROM rust:slim-bookworm AS builder

# Install build dependencies (required for Rust networking and crypto crates)
RUN apt-get update && apt-get install -y pkg-config libssl-dev build-essential

# Install the ramparts CLI directly from crates.io
RUN cargo install ramparts

# ---- Stage 2: Runtime ----
# (The rest of your Dockerfile remains exactly the same!)
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Ramparts MCP Server - AI security guardrails and safety framework"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="ramparts-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies (ca-certificates and libssl3 needed for HTTPS requests)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Copy the compiled binary from the Rust builder stage
COPY --from=builder /usr/local/cargo/bin/ramparts /usr/local/bin/ramparts

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
ENV MCP_PORT=8295
# Explicitly tell the server where to find the Rust binary
ENV RAMPARTS_BIN=/usr/local/bin/ramparts

EXPOSE 8295

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]