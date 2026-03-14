# DotDotPwn MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="DotDotPwn MCP Server - Directory traversal testing."
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="dotdotpwn-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install dependencies and DotDotPwn
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    perl \
    libwww-perl \
    liblwp-protocol-https-perl \
    tini \
    ca-certificates \
    && git clone https://github.com/wireghoul/dotdotpwn.git /opt/dotdotpwn \
    && printf '#!/bin/bash\nPERL5LIB=/opt/dotdotpwn exec perl /opt/dotdotpwn/dotdotpwn.pl "$@"\n' > /usr/local/bin/dotdotpwn \
    && chmod +x /usr/local/bin/dotdotpwn \
    && rm -rf /var/lib/apt/lists/*
    
WORKDIR /app

# Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# MCP server
COPY mcp_server.py ./

# Output directory
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

USER mcpuser

ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8223

EXPOSE 8223

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["python", "mcp_server.py"]
