# Terrascan MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

# Stage 1: Builder for the Go binary
FROM golang:1.24-bookworm AS builder
ENV CGO_ENABLED=0
# Clone the repository and build manually to respect go.mod replace directives
RUN git clone --depth 1 https://github.com/tenable/terrascan.git /go/src/terrascan
WORKDIR /go/src/terrascan
RUN go build -o /go/bin/terrascan ./cmd/terrascan

# Stage 2: Final lightweight Python environment
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Terrascan MCP Server - Infrastructure security scanner (policy-as-code)."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="terrascan-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user (creates /home/mcpuser for Terrascan's policy directory)
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies
# Git is absolutely required for 'terrascan init' to download Rego policies from GitHub
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    git \
    unzip \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the compiled binary from the builder stage
COPY --from=builder /go/bin/terrascan /usr/local/bin/terrascan

WORKDIR /app

# Copy requirements and install Python dependencies
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./
COPY hd_fetch.py ./

# Create output directory and adjust permissions
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Initialize Terrascan to download the default Rego policies into /home/mcpuser/.terrascan
# Doing this during the build prevents the first MCP scan from taking several minutes!
RUN terrascan init

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8273
# Explicitly tell the server where to find the terrascan binary
ENV TERRASCAN_BIN=/usr/local/bin/terrascan

EXPOSE 8273

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]