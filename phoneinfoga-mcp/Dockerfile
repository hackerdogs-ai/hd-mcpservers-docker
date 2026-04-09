FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then GOARCH="amd64"; elif [ "$ARCH" = "arm64" ]; then GOARCH="arm64"; else GOARCH="amd64"; fi && \
    VERSION=$(curl -sL https://api.github.com/repos/sundowndev/phoneinfoga/releases/latest | grep '"tag_name"' | head -1 | sed 's/.*"v\(.*\)".*/\1/') && \
    curl -sSL "https://github.com/sundowndev/phoneinfoga/releases/download/v${VERSION}/phoneinfoga_Linux_${GOARCH}.tar.gz" -o /tmp/pi.tar.gz && \
    tar -xzf /tmp/pi.tar.gz -C /usr/local/bin phoneinfoga && \
    chmod +x /usr/local/bin/phoneinfoga && \
    rm /tmp/pi.tar.gz
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV MCP_TRANSPORT=streamable-http
ENV MCP_PORT=8503
EXPOSE 8503
CMD ["python", "mcp_server.py"]
