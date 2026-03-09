# Nova Framework MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Nova Framework MCP Server - Automated security testing and orchestration framework"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="nova-framework-mcp"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# Install system dependencies and cleanly clone BOTH the framework and the rules
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/Nova-Hunting/nova-framework.git /opt/nova-framework \
    && git clone --depth 1 https://github.com/Nova-Hunting/nova-rules.git /opt/nova-rules

WORKDIR /app

# Copy requirements and install Python dependencies for the wrapper
# Note: Ensure fastmcp==2.14.5 is pinned in your requirements.txt!
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# FIX 1: The upstream main branch is broken (missing multiple function imports in condition.py).
# We append dummy functions for BOTH missing symbols to satisfy the import and allow the tool to boot.
RUN echo "" >> /opt/nova-framework/nova/evaluators/condition.py && \
    echo "def can_semantics_change_outcome(*args, **kwargs):" >> /opt/nova-framework/nova/evaluators/condition.py && \
    echo "    return False" >> /opt/nova-framework/nova/evaluators/condition.py && \
    echo "" >> /opt/nova-framework/nova/evaluators/condition.py && \
    echo "def can_llm_change_outcome(*args, **kwargs):" >> /opt/nova-framework/nova/evaluators/condition.py && \
    echo "    return False" >> /opt/nova-framework/nova/evaluators/condition.py

# FIX 2: Skip the upstream requirements.txt entirely! It contains hardcoded hashes that break builds,
# and it is full of developer bloat. `pip install .` will handle the core runtime dependencies natively.
RUN cd /opt/nova-framework && \
    pip install --no-cache-dir .

# Copy application code
COPY mcp_server.py ./

# Create output directory and grant permissions
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app /opt/nova-framework /opt/nova-rules

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8299
ENV NOVA_FRAMEWORK_BIN=/usr/local/bin/novarun

EXPOSE 8299

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]