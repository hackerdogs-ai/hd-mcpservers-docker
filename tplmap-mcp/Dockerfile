# Tplmap MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64
# Uses Python 3.12; tplmap's requirements install excludes wsgiref (Python 2-only, built-in to Py3).

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Tplmap MCP Server - Server-side template injection exploitation."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="tplmap-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
git tini ca-certificates \
&& rm -rf /var/lib/apt/lists/* \
&& git clone --depth 1 https://github.com/epinna/tplmap.git /opt/tplmap \
&& grep -v '^wsgiref' /opt/tplmap/requirements.txt > /tmp/tplmap-requirements.txt \
&& pip install --no-cache-dir -r /tmp/tplmap-requirements.txt \
&& ln -sf /opt/tplmap/tplmap.py /usr/local/bin/tplmap \
&& chmod +x /opt/tplmap/tplmap.py


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
ENV MCP_PORT=8267

EXPOSE 8267

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
