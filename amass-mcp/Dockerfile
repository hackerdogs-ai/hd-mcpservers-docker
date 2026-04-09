# Amass MCP - Hackerdogs Ready
FROM python:3.12-slim-bookworm
RUN groupadd -g 1000 mcpuser && useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates wget && rm -rf /var/lib/apt/lists/*
ARG AMASS_VER=5.0.1
ARG TARGETARCH
RUN case "${TARGETARCH}" in amd64) A=linux_amd64 ;; arm64) A=linux_arm64 ;; *) A=linux_amd64 ;; esac \
    && wget -q "https://github.com/owasp-amass/amass/releases/download/v${AMASS_VER}/amass_${A}.tar.gz" -O /tmp/amass.tar.gz \
    && mkdir -p /tmp/amass_extract && tar -xzf /tmp/amass.tar.gz -C /tmp/amass_extract \
    && cp -L "$(find /tmp/amass_extract -name amass -type f | head -1)" /usr/local/bin/amass \
    && chmod +x /usr/local/bin/amass && rm -rf /tmp/amass.tar.gz /tmp/amass_extract
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_server.py ./
RUN chown -R mcpuser:mcpuser /app
USER mcpuser
ENV PYTHONUNBUFFERED=1 MCP_TRANSPORT=stdio MCP_PORT=8382
EXPOSE 8382
CMD ["python", "mcp_server.py"]
