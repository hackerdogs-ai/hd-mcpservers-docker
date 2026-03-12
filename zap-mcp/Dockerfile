# OWASP ZAP MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

# Stage 1: get OWASP ZAP (zap.sh) from official image
ARG ZAP_IMAGE=ghcr.io/zaproxy/zaproxy:stable
FROM ${ZAP_IMAGE} AS zap

# Stage 2: Python + MCP server + ZAP runtime
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="OWASP ZAP MCP Server - Automated security scanning proxy (headless)."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="zap-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install Java (required by zap.sh), tini, and ca-certificates; copy ZAP from official image
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    tini \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=zap /zap /zap
ENV PATH="/zap:${PATH}"
ENV ZAP_HOME=/zap

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8231

EXPOSE 8231

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
