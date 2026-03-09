# Recon-ng MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Recon-ng MCP Server - Web reconnaissance framework (modular)."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="recon-ng-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies, including git to clone the repository
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone the Recon-ng repository directly from GitHub
RUN git clone --depth 1 https://github.com/lanmaster53/recon-ng.git /opt/recon-ng && \
    chmod +x /opt/recon-ng/recon-ng && \
    ln -s /opt/recon-ng/recon-ng /usr/local/bin/recon-ng

WORKDIR /app

# Copy requirements and install Python dependencies
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Recon-ng's specific Python dependencies
RUN pip install --no-cache-dir -r /opt/recon-ng/REQUIREMENTS

# Copy application code
COPY mcp_server.py ./

# Create output directory and the .recon-ng config folder for the non-root user
RUN mkdir -p /app/output && \
    mkdir -p /home/mcpuser/.recon-ng && \
    chown -R mcpuser:mcpuser /app /home/mcpuser

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8256
# Explicitly tell the server where to find the recon-ng binary
ENV RECON_NG_BIN=/usr/local/bin/recon-ng

EXPOSE 8256

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]