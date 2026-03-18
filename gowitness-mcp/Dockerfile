# Gowitness MCP - Hackerdogs Ready (gowitness requires Go 1.25+)
FROM golang:1.25-bookworm AS builder
RUN go install github.com/sensepost/gowitness@latest

FROM python:3.12-slim-bookworm
RUN groupadd -g 1000 mcpuser && useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser
# Chromium for screenshots; dumb-init to avoid zombie Chrome processes
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates chromium dumb-init && \
    ln -sf /usr/bin/chromium /usr/bin/google-chrome && \
    rm -rf /var/lib/apt/lists/*
COPY --from=builder /go/bin/gowitness /usr/local/bin/gowitness
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_server.py ./
RUN chown -R mcpuser:mcpuser /app
USER mcpuser
ENV PYTHONUNBUFFERED=1 MCP_TRANSPORT=stdio MCP_PORT=8397
EXPOSE 8397
ENTRYPOINT ["dumb-init", "--"]
CMD ["python", "mcp_server.py"]
