# Kube-Bench MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Kube-Bench MCP Server - CIS Kubernetes benchmark checker."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="kube-bench-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Expose Docker's target architecture argument (amd64 or arm64)
ARG TARGETARCH

# Install system dependencies (added wget and tar for downloading the release)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    git \
    unzip \
    ca-certificates \
    wget \
    tar \
    && rm -rf /var/lib/apt/lists/*

# Download and extract the correct Kube-Bench release based on architecture
ENV KUBE_BENCH_VERSION=0.8.0
RUN mkdir -p /opt/kube-bench && \
    wget -q https://github.com/aquasecurity/kube-bench/releases/download/v${KUBE_BENCH_VERSION}/kube-bench_${KUBE_BENCH_VERSION}_linux_${TARGETARCH}.tar.gz -O /tmp/kube-bench.tar.gz && \
    tar -xzf /tmp/kube-bench.tar.gz -C /opt/kube-bench && \
    ln -s /opt/kube-bench/kube-bench /usr/local/bin/kube-bench && \
    chmod -R 755 /opt/kube-bench && \
    rm /tmp/kube-bench.tar.gz

WORKDIR /app

# Copy requirements and install Python dependencies
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./
COPY hd_fetch.py ./

# Create output directory
RUN mkdir -p /app/output /app/workdir && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8253
# Explicitly tell the server where to find the kube-bench binary
ENV KUBE_BENCH_BIN=/usr/local/bin/kube-bench

EXPOSE 8253

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]