# DNSDumpster MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="DNSDumpster MCP Server - Passive DNS reconnaissance with subdomain enumeration, MX/NS/TXT records, ASN, and geolocation"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="dnsdumpster-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    git \
    graphviz \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone the DNSDumpster repository (nmmapper/dnsdumpster)
RUN git clone --depth 1 https://github.com/nmmapper/dnsdumpster.git /opt/dnsdumpster && \
    chmod +x /opt/dnsdumpster/dnsdumpster.py

WORKDIR /app

# Copy requirements and install MCP Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install DNSDumpster's Python dependencies
RUN pip install --no-cache-dir \
    requests \
    dnspython \
    simplejson \
    ip2geotools \
    ipwhois \
    wafw00f \
    graphviz

# Create wrapper script so dnsdumpster is available on PATH
COPY <<'WRAPPER' /usr/local/bin/dnsdumpster
#!/bin/bash
cd /opt/dnsdumpster
exec python dnsdumpster.py "$@"
WRAPPER
RUN chmod +x /usr/local/bin/dnsdumpster

# Copy application code
COPY mcp_server.py ./

# Create output directory
RUN mkdir -p /app/output && \
    chown -R mcpuser:mcpuser /app /opt/dnsdumpster

# Switch to non-root user
USER mcpuser

# Environment variables
ENV DNSDUMPSTER_BIN=dnsdumpster
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8216

EXPOSE 8216

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
