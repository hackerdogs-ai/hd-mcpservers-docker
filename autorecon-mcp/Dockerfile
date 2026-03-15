# AutoRecon MCP Server - Hackerdogs Ready (robust: full AutoRecon tool stack)
# Uses Kali Linux base so AutoRecon's required tools (nmap, nikto, feroxbuster, etc.) are available.

FROM kalilinux/kali-rolling

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="AutoRecon MCP Server - Automated reconnaissance with full tool stack"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="autorecon-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Install AutoRecon's required tools (per https://github.com/Tib3rius/AutoRecon)
# + python3/pip/venv, gcc/python3-dev (for psutil wheel build), tini
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    tini \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    gcc \
    git \
    seclists \
    curl \
    dnsrecon \
    enum4linux \
    feroxbuster \
    gobuster \
    impacket-scripts \
    nbtscan \
    nikto \
    nmap \
    onesixtyone \
    oscanner \
    redis-tools \
    smbclient \
    smbmap \
    snmp \
    sslscan \
    sipvicious \
    tnscmd10g \
    whatweb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kali uses PEP 668 (externally-managed); install into a venv so AutoRecon + MCP deps work
# psutil (AutoRecon dep) needs gcc/python3-dev to build; remove them after to save space
COPY requirements.txt ./
RUN python3 -m venv /app/venv \
    && /app/venv/bin/pip install --no-cache-dir -r requirements.txt \
    && /app/venv/bin/pip install --no-cache-dir "git+https://github.com/Tib3rius/AutoRecon.git" \
    && apt-get purge -y --auto-remove gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser && \
    mkdir -p /app/output && chown -R mcpuser:mcpuser /app

COPY mcp_server.py ./
RUN chown mcpuser:mcpuser /app/mcp_server.py

USER mcpuser

ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8201
# So autorecon (from venv) is on PATH when MCP server runs
ENV PATH="/app/venv/bin:${PATH}"

EXPOSE 8201

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/venv/bin/python3", "mcp_server.py"]
