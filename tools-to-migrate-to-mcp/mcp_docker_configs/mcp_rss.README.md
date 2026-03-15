# RSS MCP Server - Docker Wrapper

## Problem

The `rss-mcp` npm package has a bug: its binary file (`dist/index.js`) lacks a shebang line (`#!/usr/bin/env node`). When executed directly (via `npx` or as a binary), the shell interprets the first word `import` as a command, which resolves to ImageMagick's `import` tool instead of running the Node.js script.

**Error seen:**
```
import: delegate library support not built-in '' (X11) @ error/import.c/ImportImageCommand/1302.
Version: ImageMagick 7.1.2-3...
```

## Solution

This Docker wrapper fixes the issue by:
1. Installing `rss-mcp` globally in a Docker container
2. Using `node` explicitly to run the file: `node /usr/local/lib/node_modules/rss-mcp/dist/index.js`
3. This bypasses the shell's command resolution and runs the file directly with Node.js

## Usage

### Build the Docker Image

```python
from shared.modules.tools.mcp_docker_client import build_mcp_server_docker
import json

# Load config
with open('shared/modules/tools/mcp_docker_configs/mcp_rss.json') as f:
    config = json.load(f)

# Build Docker image and get MCP config
result = build_mcp_server_docker(config)

# Result contains:
# {
#   "name": "rss-mcp",
#   "command": "docker",
#   "args": [
#     "run",
#     "--rm",
#     "-i",
#     "--env",
#     "NODE_ENV=production",
#     "--env",
#     "NODE_OPTIONS=--no-warnings",
#     "hackerdogs-mcp-rss-mcp:latest"
#   ]
# }
```

### Use in MCP Configuration

Replace your existing `rss-mcp` configuration:

**Before (broken):**
```json
{
  "mcpServers": {
    "rss-mcp": {
      "command": "npx",
      "args": ["rss-mcp"],
      "env": {
        "NODE_OPTIONS": "--no-warnings"
      }
    }
  }
}
```

**After (fixed with Docker):**
```json
{
  "mcpServers": {
    "rss-mcp": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env",
        "NODE_ENV=production",
        "--env",
        "NODE_OPTIONS=--no-warnings",
        "hackerdogs-mcp-rss-mcp:latest"
      ]
    }
  }
}
```

## Testing

Test the build:
```bash
python3 -c "
from shared.modules.tools.mcp_docker_client import build_mcp_server_docker
import json
config = json.load(open('shared/modules/tools/mcp_docker_configs/mcp_rss.json'))
result = build_mcp_server_docker(config)
print('✅ Success!' if result else '❌ Failed')
print(json.dumps(result, indent=2))
"
```

## Docker Image

- **Image Name**: `hackerdogs-mcp-rss-mcp:latest`
- **Base Image**: `node:20-slim`
- **Size**: ~516MB (includes Node.js runtime and rss-mcp package)

## Benefits

✅ **Fixes the shebang bug** - Uses `node` explicitly to run the file  
✅ **Isolated environment** - Runs in Docker container  
✅ **No local npm conflicts** - Package installed in container only  
✅ **Consistent execution** - Same Node.js version every time  
✅ **No PATH issues** - ImageMagick's `import` not in container PATH

## Alternative Solutions

If you don't want to use Docker, you can:

1. **Report the bug** to the `rss-mcp` package maintainer to add a shebang
2. **Use a local workaround**: Install locally and run with `node`:
   ```bash
   npm install -g rss-mcp
   node $(npm root -g)/rss-mcp/dist/index.js
   ```
3. **Create a wrapper script** locally with proper shebang


