# TruffleHog MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="TruffleHog MCP Server - Git repository secret scanning."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="trufflehog-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Expose Docker's target architecture argument (amd64 or arm64)
ARG TARGETARCH

# Install system dependencies (wget/tar for downloading, git for scanning repos)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    wget \
    tar \
    git \
    && rm -rf /var/lib/apt/lists/*

# Download and extract the correct TruffleHog v3 release based on architecture
ENV TRUFFLEHOG_VERSION=3.93.7
RUN wget -q https://github.com/trufflesecurity/trufflehog/releases/download/v${TRUFFLEHOG_VERSION}/trufflehog_${TRUFFLEHOG_VERSION}_linux_${TARGETARCH}.tar.gz -O /tmp/trufflehog.tar.gz && \
    tar -xzf /tmp/trufflehog.tar.gz -C /usr/local/bin trufflehog && \
    chmod +x /usr/local/bin/trufflehog && \
    rm /tmp/trufflehog.tar.gz

WORKDIR /app

# Copy requirements and install Python dependencies
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
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
ENV MCP_PORT=8258
# Explicitly tell the server where to find the trufflehog binary
ENV TRUFFLEHOG_BIN=/usr/local/bin/trufflehog

EXPOSE 8258

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]