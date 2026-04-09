FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Open Legal Compliance MCP MCP Server"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL maintainer="support@hackerdogs.ai"
LABEL org.opencontainers.image.title="open-legal-mcp"

RUN groupadd -g 1000 mcpuser && useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser
RUN apt-get update && apt-get install -y --no-install-recommends tini ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_server.py ./
RUN chown -R mcpuser:mcpuser /app

USER mcpuser
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8439
EXPOSE 8439
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
