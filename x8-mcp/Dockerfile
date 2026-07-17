# X8 MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

# Stage 1: Builder for the Rust binary 
# (Pinned to 1.77 to prevent type-inference errors on the legacy 'time' crate)
FROM rust:1.77-slim-bookworm AS builder
# Install build dependencies required for compiling Rust network crates
RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install x8 using --locked to strictly enforce the original 1.77-compatible dependency tree
RUN cargo install x8 --locked

# Stage 2: Final lightweight Python environment
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="X8 MCP Server - Hidden parameter discovery."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="x8-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy the compiled binary from the Rust builder stage
COPY --from=builder /usr/local/cargo/bin/x8 /usr/local/bin/x8

WORKDIR /app

# Copy requirements and install Python dependencies
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
ENV MCP_PORT=8275
# Explicitly tell the server where to find the x8 binary
ENV X8_BIN=/usr/local/bin/x8

EXPOSE 8275

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]