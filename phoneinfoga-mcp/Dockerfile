FROM python:3.11-slim
# Pin release so builds do not depend on GitHub API at image-build time (rate limits / empty VERSION break tar).
ARG PHONEINFOGA_VERSION=2.11.0
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then PIARCH="Linux_x86_64"; \
    elif [ "$ARCH" = "arm64" ]; then PIARCH="Linux_arm64"; \
    else PIARCH="Linux_x86_64"; fi && \
    curl -fsSL "https://github.com/sundowndev/phoneinfoga/releases/download/v${PHONEINFOGA_VERSION}/phoneinfoga_${PIARCH}.tar.gz" -o /tmp/pi.tar.gz && \
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
