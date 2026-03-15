# 🐳 OSINT Tools Docker Setup

## Overview

This directory contains the **project's internal** Docker image for OSINT binary tools (ExifTool, Amass, Nuclei, etc.). LangChain tools in this repo (e.g. `shared/modules/tools/osint/exiftool_langchain.py`) call this container via `DockerOSINTClient` in `shared/modules/tools/docker_client.py`.

## Quick Start

### 1. Build Docker Image (from repo root)

```bash
cd shared/modules/tools/docker
docker build -t osint-tools:latest .
```

**Build time:** ~5-10 minutes (downloads and compiles tools)

### 2. Start Container (Option A: Docker Compose)

```bash
docker-compose up -d
```

### 2. Start Container (Option B: Manual)

```bash
docker run -d \
  --name osint-tools \
  -v $(pwd)/workspace:/workspace \
  osint-tools:latest
```

### 3. Verify Installation

```bash
# Check container is running
docker ps | grep osint-tools

# Test a tool
docker exec osint-tools amass -version
docker exec osint-tools nuclei -version
docker exec osint-tools subfinder -version
```

## Tools Included

The Docker image includes:

### Binary Tools (Go/C)
- ✅ **Amass** - Subdomain enumeration
- ✅ **Nuclei** - Vulnerability scanner
- ✅ **Subfinder** - Fast subdomain discovery
- ✅ **Masscan** - Port scanner
- ✅ **ZMap** - Single-packet scanner
- ✅ **waybackurls** - Wayback Machine URL fetcher
- ✅ **ExifTool** - Metadata extraction
- ✅ **YARA** - Pattern matching

### Python Tools
- ✅ **sublist3r** - Subdomain enumeration
- ✅ **dnsrecon** - DNS enumeration
- ✅ **theHarvester** - Information gathering
- ✅ **sherlock-project** - Username enumeration
- ✅ **maigret** - Advanced username search
- ✅ **ghunt** - Google account investigation
- ✅ **holehe** - Email registration checker
- ✅ **onionsearch** - Dark Web (.onion) search engine scraper
- ✅ **scrapy** - Web scraping framework
- ✅ **waybackpy** - Wayback Machine API
- ✅ **exifread** - EXIF metadata reader

## Usage in Python Code

Tools automatically detect Docker and use it if binaries aren't available on host:

```python
from hackerdogs_tools.osint.infrastructure.amass_langchain import amass_enum

# Automatically uses Docker if amass not on host
result = amass_enum(runtime, domain="example.com")
```

## Environment Variables

```bash
# Docker image name
export OSINT_DOCKER_IMAGE="osint-tools:latest"

# Container name
export OSINT_DOCKER_CONTAINER="osint-tools"

# Docker runtime (docker or podman)
export OSINT_DOCKER_RUNTIME="docker"

# Workspace directory
export OSINT_WORKSPACE="/tmp/osint-workspace"
```

## Docker Compose Configuration

The `docker-compose.yml` includes:
- **Tor Proxy Service** - Required for OnionSearch tool (Dark Web searches)
- Resource limits (CPU/memory)
- Volume mounts for workspace
- Network isolation
- Auto-restart policy

### Tor Proxy Setup

**OnionSearch** requires a Tor proxy to access Dark Web (.onion) search engines. The `docker-compose.yml` automatically includes a Tor proxy service:

```yaml
tor-proxy:
  image: dperson/torproxy:latest
  ports:
    - "9050:9050"  # SOCKS5 proxy
```

**How it works:**
1. Tor proxy runs in separate container (`tor-proxy`)
2. Exposes SOCKS5 proxy on port `9050`
3. `osint-tools` container connects via Docker network: `tor-proxy:9050`
4. OnionSearch automatically uses `--proxy tor-proxy:9050`

**Verification:**
```bash
# Check Tor is running
docker ps | grep tor-proxy

# Test Tor connection from osint-tools
docker exec osint-tools curl --socks5-hostname tor-proxy:9050 https://check.torproject.org/api/ip

# Check Tor logs
docker logs tor-proxy
```

**Note:** Tor takes ~30-60 seconds to bootstrap. The health check ensures `osint-tools` waits until Tor is ready before starting.

**Manual Setup (if not using docker-compose):**
```bash
# Run Tor proxy
docker run -d \
  --name tor-proxy \
  --network hd-tools \
  -p 9050:9050 \
  dperson/torproxy:latest

# Start osint-tools with Tor proxy
docker run -d \
  --name osint-tools \
  --network hd-tools \
  -e TOR_PROXY=tor-proxy:9050 \
  osint-tools:latest
```

## Security Considerations

1. **Container Isolation**: Tools run in isolated containers
2. **Resource Limits**: CPU and memory limits prevent resource exhaustion
3. **Network Policies**: Containers have limited network access
4. **Read-Only Filesystem**: Consider using read-only root filesystem
5. **No Privileged Mode**: Containers run without elevated privileges

## Troubleshooting

### Container Won't Start

```bash
# Check Docker logs
docker logs osint-tools

# Check if image exists
docker images | grep osint-tools

# Rebuild if needed
docker build -t osint-tools:latest .
```

### Permission Denied

```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker
```

### Tool Not Found in Container

```bash
# Enter container and check
docker exec -it osint-tools bash
which amass
which nuclei
```

### Out of Disk Space

```bash
# Clean up Docker
docker system prune -a

# Remove old images
docker image prune -a
```

## Performance

- **Container Startup**: ~1-2 seconds (if image cached)
- **Tool Execution**: Same as native (minimal overhead)
- **Parallel Execution**: Can run multiple containers

## Updating Tools

To update tools in the image:

```bash
# Rebuild image
docker build -t osint-tools:latest .

# Restart container
docker-compose restart
# Or
docker restart osint-tools
```

## Production Deployment

For production:

1. **Use Docker Registry**: Push image to registry
   ```bash
   docker tag osint-tools:latest registry.example.com/osint-tools:latest
   docker push registry.example.com/osint-tools:latest
   ```

2. **Use Orchestration**: Deploy with Kubernetes/Docker Swarm

3. **Set Resource Limits**: Adjust in docker-compose.yml

4. **Enable Logging**: Configure Docker logging driver

5. **Health Checks**: Add health check endpoints

## Alternative: Podman

If using Podman instead of Docker:

```bash
# Set environment variable
export OSINT_DOCKER_RUNTIME="podman"

# Build with podman
podman build -t osint-tools:latest .

# Run with podman
podman run -d --name osint-tools osint-tools:latest
```

---

**See `DOCKER_SETUP.md` for detailed architecture and implementation.**

