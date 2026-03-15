# 🐳 Container Deployment Guide

## Overview

This guide explains how to deploy your OSINT tools when **your application itself runs in Docker** and needs to call OSINT binaries in **another Docker container**.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│ Host Machine                             │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │ Application Container             │   │
│  │ (Your LangChain/CrewAI Agents)   │   │
│  │                                   │   │
│  │  docker exec osint-tools amass... │   │
│  └───────────────┬──────────────────┘   │
│                  │                        │
│                  │ Docker Socket           │
│                  │ /var/run/docker.sock   │
│                  ▼                        │
│  ┌──────────────────────────────────┐   │
│  │ Docker Daemon (Host)              │   │
│  └───────────────┬──────────────────┘   │
│                  │                        │
│                  ▼                        │
│  ┌──────────────────────────────────┐   │
│  │ OSINT Tools Container             │   │
│  │ (amass, nuclei, subfinder, etc.) │   │
│  └──────────────────────────────────┘   │
└──────────────────────────────────────────┘
```

**Key Point:** Your app container uses the host's Docker daemon (via socket mount) to control the OSINT tools container.

---

## 🚀 Quick Start

### Step 1: Build OSINT Tools Image (this project)

The OSINT container is part of this repo. From **repo root**:

```bash
cd shared/modules/tools/docker
docker build -t osint-tools:latest .
```

### Step 2: Start Full Stack

```bash
# Use the full-stack compose file
docker-compose -f docker-compose.full-stack.yml up -d

# Or use standard compose (includes Tor proxy for OnionSearch)
docker-compose up -d
```

**Note:** The standard `docker-compose.yml` includes a Tor proxy service required for **OnionSearch** (Dark Web search tool). If you're using the full-stack compose, you may need to add Tor proxy separately.

### Step 3: Verify

```bash
# Check both containers are running
docker ps

# Test from app container
docker exec hackerdogs-app python3 -c "
from hackerdogs_tools.osint.docker_client import DockerOSINTClient
client = DockerOSINTClient()
print(client.test())
"
```

---

## 📋 How It Works

### Docker Socket Mounting

When you mount `/var/run/docker.sock` into your app container:

1. **App container** can execute `docker` commands
2. These commands are sent to the **host's Docker daemon**
3. Host Docker daemon manages the **OSINT tools container**
4. App container can `docker exec` into OSINT container

### Code Flow

```python
# In your app container
from hackerdogs_tools.osint.docker_client import execute_in_docker

# This executes: docker exec osint-tools amass enum -d example.com
result = execute_in_docker("amass", ["enum", "-d", "example.com"])
```

**What happens:**
1. `docker_client.py` runs `docker exec osint-tools amass ...`
2. Command goes to host Docker daemon (via socket)
3. Host Docker executes command in `osint-tools` container
4. Output returned to app container

---

## 🔒 Security Considerations

### ⚠️ Important Security Note

Mounting `/var/run/docker.sock` gives your app container **full control** over the host's Docker daemon:

- Can create/delete any container
- Can access host filesystem
- Can escape container isolation
- Can access other containers

### Security Best Practices

1. **Use Read-Only Socket** (if supported by your Docker version)
2. **Limit Container Capabilities**
3. **Use Docker Context/Namespace Isolation**
4. **Run in Isolated Network**
5. **Use Docker API Authentication** (for production)

### Example: Limited Capabilities

```yaml
services:
  app:
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro  # Read-only
    cap_drop:
      - ALL
    cap_add:
      - NET_ADMIN  # Only if needed
```

---

## 📝 Docker Compose Configuration

### Full Stack Setup

```yaml
version: '3.8'

services:
  app:
    build: .
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Required!
      - ./workspace:/workspace
    environment:
      - OSINT_DOCKER_IMAGE=osint-tools:latest
      - OSINT_DOCKER_CONTAINER=osint-tools
    depends_on:
      - osint-tools

  osint-tools:
    build:
      context: ./hackerdogs_tools/osint/docker
    image: osint-tools:latest
    volumes:
      - ./workspace:/workspace
    command: tail -f /dev/null
```

### Key Points

1. **Socket Mount**: `-v /var/run/docker.sock:/var/run/docker.sock`
2. **Shared Volume**: Both containers share `/workspace`
3. **Dependencies**: App depends on OSINT container
4. **Environment**: Set Docker image/container names

---

## 🧪 Testing

### Test Docker Socket Access

```bash
# From app container
docker exec hackerdogs-app docker ps
```

Should show running containers (including `osint-tools`).

### Test OSINT Tool Execution

```bash
# From app container
docker exec hackerdogs-app python3 -c "
from hackerdogs_tools.osint.infrastructure.amass_langchain import amass_enum
from langchain.tools import ToolRuntime

runtime = ToolRuntime(state={'user_id': 'test'})
result = amass_enum(runtime, domain='example.com')
print(result)
"
```

---

## 🐛 Troubleshooting

### Issue: "Docker not available in container"

**Problem:** App container can't access Docker.

**Solution:**
```yaml
# Add to docker-compose.yml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

### Issue: "Permission denied" on Docker socket

**Problem:** Container user doesn't have permission.

**Solution:**
```bash
# Add user to docker group (on host)
sudo usermod -aG docker $USER

# Or run container with specific user
docker run -u $(id -u):$(id -g) ...
```

### Issue: "Container osint-tools not found"

**Problem:** OSINT container not running.

**Solution:**
```bash
# Start OSINT container
docker-compose up -d osint-tools

# Or manually
docker run -d --name osint-tools osint-tools:latest
```

### Issue: "OnionSearch not working (Tor proxy)"

**Problem:** OnionSearch requires Tor proxy but it's not running.

**Solution:**
```bash
# Check Tor proxy is running
docker ps | grep tor-proxy

# Check Tor logs
docker logs tor-proxy

# Test Tor connection
docker exec osint-tools curl --socks5-hostname tor-proxy:9050 https://check.torproject.org/api/ip

# Restart Tor proxy
docker-compose restart tor-proxy
```

---

## 🔄 Alternative: Sidecar Pattern

For production, consider **Sidecar Pattern** (no socket mounting):

```yaml
services:
  app:
    # No socket mount
    volumes:
      - ./workspace:/workspace
    
  osint-worker:
    image: osint-tools:latest
    volumes:
      - ./workspace:/workspace
    # Worker watches for tasks in shared volume
    command: python3 /app/worker.py
```

**Communication:**
- App writes task to `/workspace/tasks/task.json`
- Worker reads task, executes, writes result
- App reads result from `/workspace/results/`

**Benefits:**
- ✅ No Docker socket access needed
- ✅ Better security
- ✅ Easier to scale

---

## 🔒 Tor Proxy for OnionSearch

**OnionSearch** (Dark Web search tool) requires a Tor proxy to access .onion sites. The `docker-compose.yml` includes a Tor proxy service:

```yaml
tor-proxy:
  image: dperson/torproxy:latest
  ports:
    - "9050:9050"  # SOCKS5 proxy
```

**How it works:**
- Tor proxy runs in separate container
- `osint-tools` connects via Docker network: `tor-proxy:9050`
- OnionSearch automatically uses `--proxy tor-proxy:9050`
- Health check ensures Tor is ready before OSINT tools start

**Verification:**
```bash
# Check Tor is running
docker ps | grep tor-proxy

# Test Tor from osint-tools
docker exec osint-tools curl --socks5-hostname tor-proxy:9050 https://check.torproject.org/api/ip
```

**See `docker/README.md` for detailed Tor proxy setup.**

---

## ✅ Summary

**Yes, tools in Docker can call binaries in another Docker container!**

**Requirements:**
1. Mount Docker socket: `-v /var/run/docker.sock:/var/run/docker.sock`
2. Both containers on same Docker network
3. Shared volume for file I/O (optional)
4. **Tor proxy** (for OnionSearch) - automatically included in docker-compose.yml

**Your `docker_client.py` already supports this!** Just mount the socket when running your app in Docker.

---

**See `DOCKER_IN_DOCKER.md` for detailed architecture explanation.**

