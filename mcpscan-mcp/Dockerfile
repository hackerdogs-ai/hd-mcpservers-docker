# MCPScan MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="MCPScan MCP Server - MCP server security scanning and vulnerability detection"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="mcpscan-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies and cleanly clone the repo
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/antgroup/MCPScan.git /opt/mcpscan

WORKDIR /app

# Copy requirements and install Python dependencies for the MCP server wrapper
COPY requirements.txt ./
# Explicitly install Semgrep, which is the core engine for MCPScan's taint analysis
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir semgrep

# Install MCPScan cleanly without silent failure masking
RUN cd /opt/mcpscan && \
    if [ -f "requirements.txt" ]; then pip install --no-cache-dir -r requirements.txt; fi && \
    pip install --no-cache-dir .

# Copy application code
COPY mcp_server.py ./

# Create output directory and grant permissions
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app /opt/mcpscan

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8296
ENV MCPSCAN_BIN=/usr/local/bin/mcpscan

# FIX: Provide a dummy key to bypass the global LLMClient instantiation crash at import time!
# You must pass your real key at runtime via your MCP client configuration.
ENV DEEPSEEK_API_KEY="sk-xxxxxx"

EXPOSE 8296

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]