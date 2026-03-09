# Aquatone MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Aquatone MCP Server - Visual inspection of websites across hosts."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="aquatone-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Expose Docker's target architecture argument (amd64 or arm64)
ARG TARGETARCH

# Install system dependencies, including Chromium for headless browser screenshotting
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    wget \
    unzip \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Download and extract the correct Aquatone release based on architecture
ENV AQUATONE_VERSION=1.7.0
RUN wget -q https://github.com/michenriksen/aquatone/releases/download/v${AQUATONE_VERSION}/aquatone_linux_${TARGETARCH}_${AQUATONE_VERSION}.zip -O /tmp/aquatone.zip && \
    unzip -q /tmp/aquatone.zip aquatone -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/aquatone && \
    rm /tmp/aquatone.zip

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
ENV MCP_PORT=8259
# Explicitly tell the server where to find the aquatone binary
ENV AQUATONE_BIN=/usr/local/bin/aquatone

EXPOSE 8259

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]