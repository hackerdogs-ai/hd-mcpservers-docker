# Publish MCP Docker Images to Docker Hub

This script (`publish_mcpservers_docker.sh`) builds and publishes Hackerdogs MCP Docker images to public Docker Hub under the `hackerdogs` account.

**Note**: `osint-tools` is handled separately via `docker/publish_osint_tools.sh` because it's a large build that would block other images.

## Overview

The script publishes **6 Docker images** (MCP servers and mitre-attack-mcp):

1. **`hackerdogs/hackerdogs-mcp-ocr:latest`**
   - OCR MCP Server for extracting text from images using Tesseract OCR
   - Built from: `mcp_docker_configs/mcp_ocr.json`
   - Base image: `python:3.11-slim`
   - Package: `mcp-ocr` (PyPI)
   - Build type: MCP (Python build function)

2. **`hackerdogs/hackerdogs-mcp-pdf-reader-sylphx:latest`**
   - PDF Reader MCP Server for extracting text from PDF files
   - Built from: `mcp_docker_configs/mcp_pdf_reader_sylphx.json`
   - Base image: `node:20-slim`
   - Package: `@sylphx/pdf-reader-mcp` (npm)
   - Build type: MCP (Python build function)

3. **`hackerdogs/hackerdogs-mcp-rss-mcp:latest`**
   - RSS MCP Server for RSS feed processing
   - Built from: `mcp_docker_configs/mcp_rss.json`
   - Build type: MCP (Python build function)

4. **`hackerdogs/hackerdogs-mcp-builtwith:latest`**
   - BuiltWith MCP Server for identifying technology stack behind websites
   - Built from: `mcp_docker_configs/mcp_builtwith.json`
   - Base image: `node:20-slim`
   - Source: Local file `shared/modules/tools/osint/builtwith/bw-mcp-v1.js`
   - Build type: MCP (Python build function with custom Dockerfile)
   - Requires: `BUILTWITH_API_KEY` environment variable

5. **`hackerdogs/hackerdogs-mcp-pagespeed:latest`**
   - PageSpeed MCP Server for comprehensive web performance analysis
   - Built from: `mcp_docker_configs/mcp_pagespeed.json`
   - Base image: `node:20-slim`
   - Source: Local files `shared/modules/tools/osint/pagespeed-mcp/`
   - Build type: MCP (Python build function with custom Dockerfile)
   - Requires: `PAGESPEED_API_KEY` environment variable (optional but recommended)

6. **`hackerdogs/hackerdogs-mcp-youtube:latest`**
   - YouTube MCP Server for YouTube data extraction
   - Built from: `mcp_docker_configs/mcp_youtube.json`
   - Build type: MCP (Python build function)

7. **`hackerdogs/hackerdogs-mitre-attack-mcp:latest`**
   - MITRE ATT&CK MCP Server for threat intelligence
   - Built from: `mitre-attack-mcp/Dockerfile`
   - Build type: Dockerfile (direct Docker build)

## ⚠️ Important: osint-tools is Separate

**`hackerdogs/osint-tools:latest`** is **NOT** included in this script because:
- It's a **large build** (10-15 minutes) that would block other images
- It contains many heavy dependencies (Go tools, Python packages, etc.)
- It should be built and published separately to avoid blocking other containers

**To build and publish osint-tools separately, use:**
```bash
cd shared/modules/tools
./docker/publish_osint_tools.sh hackerdogs <version>
```

This separation allows:
- ✅ Other MCP images to build quickly in parallel
- ✅ osint-tools to be built independently when needed
- ✅ No blocking of other container builds

## Prerequisites

1. **Docker** must be installed and running
2. **Docker Hub account** - You must be logged in to the `hackerdogs` account
3. **Python 3** with required dependencies installed
4. **Project dependencies** - The `mcp_docker_client.py` module must be accessible

## Usage

### Basic Usage

```bash
cd /path/to/hackerdogs-core
./shared/modules/tools/publish_mcpservers_docker.sh
```

### What the Script Does

1. **Checks prerequisites**
   - Verifies Docker is running
   - Checks if you're logged into Docker Hub (prompts for login if not)

2. **Builds images**
   - Builds each Docker image using the Python `build_mcp_server_docker()` function
   - Uses the configuration files from `mcp_docker_configs/`

3. **Tags images**
   - Tags local images as `hackerdogs/hackerdogs-mcp-{name}:latest`
   - Example: `hackerdogs-mcp-ocr:latest` → `hackerdogs/hackerdogs-mcp-ocr:latest`

4. **Pushes to Docker Hub**
   - Pushes all tagged images to public Docker Hub repository

## Docker Hub Login

Before running the script, ensure you're logged into Docker Hub:

```bash
docker login
# Enter your Docker Hub username and password
```

Or login specifically for the hackerdogs account:

```bash
docker login -u hackerdogs
```

## Example Output

```
[INFO] =========================================
[INFO] Hackerdogs MCP Docker Images Publisher
[INFO] =========================================

[SUCCESS] Docker is running
[SUCCESS] Logged into Docker Hub
[INFO] Found 5 Docker image(s) to publish:
  - hackerdogs-mcp-ocr:latest
  - hackerdogs-mcp-pdf-reader-sylphx:latest
  - hackerdogs-mcp-builtwith:latest
  - hackerdogs-mcp-pagespeed:latest
  - osint-tools:latest

[INFO] =========================================
[INFO] Processing: ocr
[INFO] Local image: hackerdogs-mcp-ocr:latest
[INFO] Docker Hub: hackerdogs/hackerdogs-mcp-ocr:latest
[INFO] =========================================
[INFO] Building image for ocr...
✅ Image built successfully
[SUCCESS] Image built: hackerdogs-mcp-ocr:latest
[INFO] Tagging hackerdogs-mcp-ocr:latest as hackerdogs/hackerdogs-mcp-ocr:latest...
[SUCCESS] Tagged: hackerdogs/hackerdogs-mcp-ocr:latest
[INFO] Pushing hackerdogs/hackerdogs-mcp-ocr:latest to Docker Hub...
[SUCCESS] Pushed: hackerdogs/hackerdogs-mcp-ocr:latest
[SUCCESS] Completed: ocr

...

[SUCCESS] All images published successfully! 🎉
```

## Using Published Images

After publishing, you can use the images directly from Docker Hub:

### OCR Server Example

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
        "hackerdogs/hackerdogs-mcp-ocr:latest"
      ]
    }
  }
}
```

### BuiltWith Server Example

```json
{
  "mcpServers": {
    "builtwith": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env",
        "BUILTWITH_API_KEY=your-api-key-here",
        "hackerdogs/hackerdogs-mcp-builtwith:latest"
      ]
    }
  }
}
```

**Note:** Replace `your-api-key-here` with your actual BuiltWith API key from [api.builtwith.com](https://api.builtwith.com/).

### PageSpeed Server Example

```json
{
  "mcpServers": {
    "pagespeed": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env",
        "PAGESPEED_API_KEY=your-api-key-here",
        "hackerdogs/hackerdogs-mcp-pagespeed:latest"
      ]
    }
  }
}
```

**Note:** Replace `your-api-key-here` with your actual Google PageSpeed Insights API key from [Google Cloud Console](https://console.cloud.google.com/). The API key is optional but recommended for higher rate limits.

## Troubleshooting

### Docker not running
```bash
# Start Docker Desktop or Docker daemon
# On macOS: Open Docker Desktop
# On Linux: sudo systemctl start docker
```

### Not logged into Docker Hub
```bash
docker login
# The script will also prompt you if not logged in
```

### Build failures
- Ensure all Python dependencies are installed
- Check that the config files exist in `mcp_docker_configs/`
- Verify network connectivity for downloading base images and packages

### Push failures
- Verify you have write access to the `hackerdogs` Docker Hub organization
- Check Docker Hub rate limits (if you hit them, wait and retry)
- Ensure the image was tagged correctly before pushing

## Updating Images

To update and republish images:

```bash
# The script will rebuild images with force_rebuild=True
./shared/modules/tools/publish_mcpservers_docker.sh
```

## Related Files

- **Script**: `shared/modules/tools/publish_mcpservers_docker.sh`
- **Docker Client**: `shared/modules/tools/mcp_docker_client.py`
- **OCR Config**: `shared/modules/tools/mcp_docker_configs/mcp_ocr.json`
- **PDF Reader Config**: `shared/modules/tools/mcp_docker_configs/mcp_pdf_reader_sylphx.json`
- **BuiltWith Config**: `shared/modules/tools/mcp_docker_configs/mcp_builtwith.json`
- **PageSpeed Config**: `shared/modules/tools/mcp_docker_configs/mcp_pagespeed.json`
- **OSINT Tools Script**: `shared/modules/tools/docker/publish_osint_tools.sh`
- **OSINT Tools Dockerfile**: `shared/modules/tools/docker/Dockerfile`

## Notes

- Images are published as **public** repositories on Docker Hub
- The `:latest` tag is used for all images
- Local images are preserved after publishing (not removed)
- The script uses `force_rebuild=True` to ensure fresh builds

