# RustScan MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

# 1. Use the official RustScan image as a temporary "extractor" stage
FROM rustscan/rustscan:2.1.1 AS rustscan-bin

# 2. Main Wfuzz MCP Server - Hackerdogs Ready
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.title="rustscan-mcp"

# 3. Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# 4. Install Runtime Dependencies
# RustScan REQUIRES nmap to function
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    nmap \
    && rm -rf /var/lib/apt/lists/*

# 5. TODO: Install rustscan
# Copy the pre-built binary from the first stage
COPY --from=rustscan-bin /usr/local/bin/rustscan /usr/local/bin/rustscan

WORKDIR /app

# 6. Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# 7. Copy application code
COPY mcp_server.py ./

# 8. Create output directory and fix permissions
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8200

EXPOSE 8200

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
