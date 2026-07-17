FROM node:20-slim
WORKDIR /app

# Python 3 for mcp_http_proxy.py; dnstwist installed as a native binary.
# Farm MCP containers have no Docker daemon, so dnstwist runs directly here
# rather than via the upstream package's `docker run elceef/dnstwist …`.
# dnstwist's optional features (mxcheck, banners, geoip, whois, fuzzy hashing) need
# these Python libs; --no-install-recommends would otherwise drop them.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 dnstwist \
    python3-dnspython python3-tld python3-requests \
    python3-geoip python3-whois python3-ssdeep \
    && rm -rf /var/lib/apt/lists/*

# Docker shim: forwards the upstream's `docker run … elceef/dnstwist <args>`
# calls to the native dnstwist binary (and answers its version/image checks).
COPY docker-shim.sh /usr/local/bin/docker
RUN sed -i 's/\r$//' /usr/local/bin/docker && chmod +x /usr/local/bin/docker

# Install the MCP server and supergateway
RUN npm install -g @burtthecoder/mcp-dnstwist supergateway || npm install -g supergateway

COPY mcp_http_proxy.py /mcp_http_proxy.py
COPY entrypoint.sh /entrypoint.sh

# Fix Windows line endings and set execution permissions
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=8636
EXPOSE 8636

ENTRYPOINT ["/entrypoint.sh"]
