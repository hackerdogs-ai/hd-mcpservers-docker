# Falco MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Falco MCP Server - Runtime security monitoring (containers/K8s)."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="falco-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# 1. Install system prerequisites
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    git \
    unzip \
    ca-certificates \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 2. Add Falco's GPG key and official repository
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://falco.org/repo/falcosecurity-packages.asc | gpg --dearmor -o /etc/apt/keyrings/falco.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/falco.gpg] https://download.falco.org/packages/deb stable main" > /etc/apt/sources.list.d/falcosecurity.list

# 3. Prevent apt-get from pausing for user input and explicitly disable driver compilation
ENV FALCO_FRONTEND=noninteractive
ENV FALCO_DRIVER_CHOICE=none

# 4. Install the standard falco package (which will now skip the kernel DKMS build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    falco \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./
COPY hd_fetch.py ./

# Create output directory and ensure mcpuser has access to Falco's rule directories
RUN mkdir -p /app/output && \
    chown -R mcpuser:mcpuser /app /etc/falco

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8271
# Explicitly tell the server where to find the falco binary
ENV FALCO_BIN=/usr/bin/falco

EXPOSE 8271

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]