# Tools Web Service - PRD compliant
# Multi-arch: linux/amd64, linux/arm64 (Mac & Linux, ARM & AMD)
# Includes: Python, Docker CLI, Node.js (npx), uv (uvx)

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="Tools Web Service - MCP tools catalog and run API"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL maintainer="support@hackerdogs.ai"
LABEL org.opencontainers.image.title="tools-webservice"
LABEL org.opencontainers.image.licenses="Apache-2.0"

# Install Docker CLI (for running tool containers), Node.js (npx), uv (uvx), tini
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Docker CLI - multi-arch (deb arch -> Docker arch: amd64->x86_64, arm64->aarch64)
ARG DOCKER_VERSION=27.3.1
RUN set -e; \
    case "$$(dpkg --print-architecture)" in amd64) DARCH=x86_64;; arm64) DARCH=aarch64;; *) DARCH=x86_64;; esac; \
    curl -fsSL "https://download.docker.com/linux/static/stable/$${DARCH}/docker-${DOCKER_VERSION}.tgz" | tar xzvf - --strip-components=1 -C /usr/local/bin docker/docker

# Node.js 20 LTS (for npx tools)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# uv (for uvx tools)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && cp -a /root/.local/bin/uv /usr/local/bin/ \
    && (cp -a /root/.local/bin/uvx /usr/local/bin/ 2>/dev/null || true)

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY run.py ./

# Optional: non-root user (Docker socket may need root or docker group on host)
# RUN groupadd -g 1000 appuser && useradd -u 1000 -g appuser -m -s /bin/bash appuser
# USER appuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8000

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "run.py"]
