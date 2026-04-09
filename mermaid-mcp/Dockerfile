FROM node:20-slim AS mermaid
RUN npm install -g @mermaid-js/mermaid-cli

FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Mermaid MCP Server - render Mermaid diagrams to SVG or PNG"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL maintainer="support@hackerdogs.ai"
LABEL mcp-server-scope="remote"
LABEL org.opencontainers.image.title="mermaid-mcp"

COPY --from=mermaid /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=mermaid /usr/local/bin/node /usr/local/bin/node
RUN ln -s /usr/local/lib/node_modules/.bin/mmdc /usr/local/bin/mmdc

RUN groupadd -g 1000 mcpuser && useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

RUN apt-get update && apt-get install -y --no-install-recommends tini ca-certificates chromium \
    && rm -rf /var/lib/apt/lists/*

ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_server.py ./
RUN chown -R mcpuser:mcpuser /app

USER mcpuser
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8524
EXPOSE 8524
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
