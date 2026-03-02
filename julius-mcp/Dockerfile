FROM golang:1.25-bookworm AS builder
RUN go install github.com/praetorian-inc/julius/cmd/julius@latest

FROM python:3.12-slim-bookworm
LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Julius MCP Server - LLM Service Fingerprinting"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"

RUN groupadd -g 1000 mcpuser && useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser
RUN apt-get update && apt-get install -y --no-install-recommends tini ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /go/bin/julius /usr/local/bin/julius
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_server.py ./
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app
USER mcpuser
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8100
EXPOSE 8100
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "mcp_server.py"]
