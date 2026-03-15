# MCP Docker Client - Generic Docker Wrapper for MCP Servers

## Overview

The `mcp_docker_client.py` module provides a generic Docker-based execution layer for MCP servers. It can dynamically build Docker images and run MCP servers in isolated containers **without disrupting existing Docker infrastructure**.

## Features

✅ **Dynamic Image Building**: Automatically builds Docker images from PyPI packages or custom Dockerfiles  
✅ **On-Demand Execution**: Creates containers on-demand and cleans them up automatically  
✅ **Isolated from Existing Infrastructure**: Uses separate image naming (`hackerdogs-mcp-*`) and build cache  
✅ **No Local Installation Required**: MCP servers run in containers, no need to install on host  
✅ **Support for Complex Dependencies**: Handles system packages, custom Dockerfiles, and environment variables  

## Quick Start

### Example: mcp-ocr

```python
from shared.modules.tools.mcp_docker_client import build_mcp_server_docker
import json

# Define MCP server configuration
mcp_config = {
    "name": "ocr",
    "package_name": "mcp-ocr",
    "base_image": "python:3.11-slim",
    "additional_packages": ["tesseract-ocr", "tesseract-ocr-eng"],
    "entrypoint": "python -m mcp_ocr"
}

# Build image and get Docker configuration
docker_config = build_mcp_server_docker(mcp_config)

# Use in your MCP config
mcp_servers = {
    "mcpServers": {
        docker_config["name"]: {
            "command": docker_config["command"],
            "args": docker_config["args"]
        }
    }
}

print(json.dumps(mcp_servers, indent=2))
```

## Configuration Options

### Basic Configuration (Pip Package)

```python
{
    "name": "server-name",              # Server name (used for image: hackerdogs-mcp-{name}:latest)
    "package_name": "pypi-package",      # PyPI package to install
    "base_image": "python:3.11-slim",   # Base Docker image (optional)
    "additional_packages": ["pkg1", "pkg2"],  # System packages via apt-get (optional)
    "entrypoint": "python -m module",   # Entrypoint command (optional, auto-detected)
    "env": {                            # Environment variables (optional)
        "KEY": "value"
    }
}
```

### Custom Dockerfile Configuration

```python
{
    "name": "server-name",
    "dockerfile": """
FROM python:3.11-slim
RUN apt-get update && apt-get install -y package1 package2
RUN pip install my-package
ENTRYPOINT ["python", "-m", "my_module"]
""",
    "build_context": "/optional/path"  # Optional build context directory
}
```

## Architecture

### Image Naming
- Format: `hackerdogs-mcp-{server-name}:latest`
- Example: `hackerdogs-mcp-ocr:latest`
- **Does not conflict** with existing Docker images

### Build Cache
- Location: `~/.hackerdogs/mcp-docker-builds/`
- Stores Dockerfiles and build contexts
- Separate from existing Docker infrastructure

### Container Lifecycle
- Containers are created with `--rm` flag (auto-removed after execution)
- Interactive mode (`-i`) for stdio communication
- Environment variables passed via `--env` flags

## Testing

Run the test suite:

```bash
python shared/modules/tools/tests/test_mcp_docker_ocr.py
```

This will:
1. ✅ Build Docker image for mcp-ocr from pip package
2. ✅ Build Docker image from custom Dockerfile
3. ✅ Generate MCP configuration JSON
4. ✅ Verify Docker images exist

## Integration with Existing System

### No Conflicts
- **Separate image namespace**: `hackerdogs-mcp-*` vs existing `osint-tools-*`
- **Separate build cache**: `~/.hackerdogs/mcp-docker-builds/` vs existing Dockerfiles
- **Separate module**: `mcp_docker_client.py` vs `docker_client.py`

### Can Coexist
- Both systems can run simultaneously
- Different use cases:
  - `docker_client.py`: OSINT command-line tools
  - `mcp_docker_client.py`: MCP servers

## API Reference

### `build_mcp_server_docker(mcp_config, force_rebuild=False)`

Build Docker image and generate MCP server configuration.

**Parameters:**
- `mcp_config` (dict): MCP server configuration
- `force_rebuild` (bool): Force rebuild even if image exists

**Returns:**
- `dict`: MCP server configuration with Docker command, or `None` if failed

### `get_mcp_docker_client()`

Get or create global MCP Docker client instance.

**Returns:**
- `MCPDockerClient`: Client instance, or `None` if Docker unavailable

## Example Configurations

### mcp-ocr (Tested ✅)

```json
{
  "name": "ocr",
  "package_name": "mcp-ocr",
  "base_image": "python:3.11-slim",
  "additional_packages": ["tesseract-ocr", "tesseract-ocr-eng"],
  "entrypoint": "python -m mcp_ocr"
}
```

### Any PyPI MCP Server

```json
{
  "name": "my-server",
  "package_name": "mcp-my-server",
  "base_image": "python:3.11-slim"
}
```

### Custom Dockerfile

```json
{
  "name": "custom-server",
  "dockerfile": "FROM python:3.11-slim\nRUN pip install my-package\nENTRYPOINT [\"python\", \"-m\", \"my_module\"]"
}
```

## Generated MCP Configuration

The system generates MCP-compatible configuration:

```json
{
  "mcpServers": {
    "ocr": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env",
        "PYTHONUNBUFFERED=1",
        "hackerdogs-mcp-ocr:latest"
      ]
    }
  }
}
```

**Note:** Container names (`--name`) are omitted to allow Docker to auto-generate unique names. This prevents conflicts when multiple discovery calls happen concurrently. Containers are ephemeral (`--rm`) so names don't need to be predictable.

This can be directly added to:
- `~/.cursor/mcp.json` (Cursor)
- `~/.claude.json` (Claude Desktop)
- `~/.config/mcp/servers/*.json` (Standard MCP)

## Troubleshooting

### Docker Not Available
- Ensure Docker is running: `docker ps`
- Check Docker socket permissions

### Build Failures
- Check logs in `logs/mcp_docker_client.log`
- Verify package name is correct
- Ensure base image is accessible

### Image Already Exists
- Use `force_rebuild=True` to rebuild
- Or manually remove: `docker rmi hackerdogs-mcp-{name}:latest`

## Future Enhancements

Potential improvements:
- [ ] Support for npm-based MCP servers
- [ ] Automatic dependency detection
- [ ] Multi-architecture builds
- [ ] Image caching and versioning
- [ ] Health checks and monitoring

