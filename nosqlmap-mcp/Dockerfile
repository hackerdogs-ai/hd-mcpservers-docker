# NoSQLMap MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="NoSQLMap MCP Server - NoSQL injection testing."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="nosqlmap-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/codingo/NoSQLMap.git /opt/NoSQLMap \
    && 2to3 -w -n /opt/NoSQLMap/*.py 2>/dev/null || true \
    && sed -i 's/\.database_names()/.list_database_names()/g' /opt/NoSQLMap/*.py \
    && sed -i 's/\.collection_names()/.list_collection_names()/g' /opt/NoSQLMap/*.py \
    && sed -i "s/except NoSQLMapException, e:/except NoSQLMapException as e:/g" /opt/NoSQLMap/*.py \
    && pip install --no-cache-dir \
        'pymongo>=3.7,<5.0' \
        'httplib2>=0.19.0' \
        'ipcalc>=1.1.3' \
        'pbkdf2>=1.3' \
        'requests' \
        'CouchDB>=1.1' \
        'six'

COPY <<'WRAPPER' /usr/local/bin/nosqlmap
#!/bin/bash
cd /opt/NoSQLMap
exec python nosqlmap.py "$@"
WRAPPER
RUN chmod +x /usr/local/bin/nosqlmap

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
ENV MCP_PORT=8266

EXPOSE 8266

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
