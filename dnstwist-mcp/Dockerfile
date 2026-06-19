FROM node:20-slim
WORKDIR /app

# 1. Install Python 3 (Required for mcp_http_proxy.py)
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*

# 2. Create a dummy docker binary to prevent the Node app from crashing 
# when it checks if Docker is installed (ENOENT error).
RUN echo '#!/bin/sh\necho "Docker version 24.0.0"\nexit 0' > /usr/local/bin/docker && \
    chmod +x /usr/local/bin/docker

# 3. Install the MCP server and supergateway
RUN npm install -g @burtthecoder/mcp-dnstwist supergateway || npm install -g supergateway

COPY mcp_http_proxy.py /mcp_http_proxy.py
COPY entrypoint.sh /entrypoint.sh

# 4. Fix Windows line endings and set execution permissions
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8636
EXPOSE 8636

ENTRYPOINT ["/entrypoint.sh"]