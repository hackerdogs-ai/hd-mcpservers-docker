# Docker MCP Toolkit Gateway Configuration

## Overview

This configuration connects to the **Docker MCP Toolkit Gateway**, which is a management interface integrated into Docker Desktop that simplifies the setup, management, and execution of containerized MCP (Model Context Protocol) servers.

## Configuration

**File:** `mcp_docker.json`

```json
{
  "mcpServers": {
    "MCP_DOCKER": {
      "command": "docker",
      "args": ["mcp", "gateway", "run"],
      "description": "Docker MCP Toolkit Gateway - Provides access to containerized MCP servers from the Docker MCP Catalog"
    }
  }
}
```

## Verification

✅ **Configuration is CORRECT** - Verified against:
- Docker MCP Toolkit official documentation: [docs.docker.com](https://docs.docker.com/ai/mcp-catalog-and-toolkit/toolkit/)
- Active Cursor MCP configuration (`~/.cursor/mcp.json`)
- MCP protocol stdio specification

## What is Docker MCP Toolkit?

The Docker MCP Toolkit is a feature within Docker Desktop that:

- **Simplifies MCP Server Management**: Browse and launch MCP servers directly from the Docker MCP Catalog
- **Zero Manual Setup**: Eliminates dependency management and runtime configuration
- **Server Aggregation**: Functions as both an MCP server aggregator and gateway
- **Cross-LLM Compatibility**: Works with Claude, Cursor, and other MCP clients
- **Dynamic MCP**: Enables AI agents to discover and add MCP servers on-demand

## Key Features

### Security
- **Passive Security**: All `mcp/*` namespace images are built by Docker and digitally signed
- **Active Security**: Runtime resource and access limitations (CPU, memory, filesystem restrictions)
- **SBOM**: Software Bill of Materials included for transparency

### OAuth Authentication
- Automatic OAuth handling for services like GitHub, Notion, Linear
- Browser-based authorization
- Secure credential management

### Resource Limits
- Default: 1 CPU, 2 GB memory per MCP tool
- Filesystem access restrictions
- Network access controls

## Usage

### Prerequisites

1. **Docker Desktop** must be installed and running
2. **Docker MCP Toolkit** must be enabled in Docker Desktop
3. **MCP servers** must be added via Docker Desktop's MCP Toolkit interface

### Setup Steps

1. **Enable Docker MCP Toolkit**:
   - Open Docker Desktop
   - Navigate to MCP Toolkit section
   - Ensure the gateway is running

2. **Add MCP Servers**:
   - Browse the Docker MCP Catalog in Docker Desktop
   - Add desired MCP servers (e.g., GitHub Official, Puppeteer, etc.)
   - Configure authentication if needed (OAuth handled automatically)

3. **Connect MCP Client**:
   - Add this configuration to your MCP client (Cursor, Claude Desktop, etc.)
   - The gateway will expose all installed MCP servers

### Example: Using with Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "MCP_DOCKER": {
      "command": "docker",
      "args": ["mcp", "gateway", "run"]
    }
  }
}
```

### Example: Using with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `~/.config/claude/claude_desktop_config.json` (Linux):

```json
{
  "mcpServers": {
    "MCP_DOCKER": {
      "command": "docker",
      "args": ["mcp", "gateway", "run"]
    }
  }
}
```

## How It Works

1. **Gateway Command**: `docker mcp gateway run` starts the MCP gateway
2. **Server Discovery**: Gateway discovers MCP servers added via Docker Desktop
3. **Aggregation**: Gateway aggregates all installed servers into a single MCP endpoint
4. **Client Connection**: MCP clients connect to the gateway via stdio
5. **Tool Execution**: Tools are executed in isolated containers with resource limits

## Available MCP Servers

The gateway provides access to all MCP servers installed via Docker Desktop's MCP Toolkit, including:

- **GitHub Official**: Interact with GitHub repositories and issues
- **Puppeteer**: Web automation and screenshot capabilities
- **Filesystem**: File system operations
- **PostgreSQL**: Database queries
- **And many more** from the Docker MCP Catalog

## Troubleshooting

### Gateway Not Starting

1. Ensure Docker Desktop is running
2. Check if Docker MCP Toolkit is enabled in Docker Desktop settings
3. Verify Docker CLI is accessible: `docker --version`
4. Test gateway command: `docker mcp gateway run` (should start stdio server)

### Servers Not Available

1. Open Docker Desktop → MCP Toolkit
2. Verify servers are added in the Catalog tab
3. Check server status (should be "Running" or "Available")
4. For OAuth servers, ensure authentication is completed

### Authentication Issues

1. For OAuth-enabled servers (GitHub, Notion, etc.):
   - Open Docker Desktop → MCP Toolkit
   - Navigate to server's Configuration tab
   - Complete OAuth flow in browser
   - Credentials are managed automatically

### Network/Registry Access

- Ensure `docker login` is completed for private registries
- Check network connectivity for pulling images
- Verify Docker Hub access for `mcp/*` namespace images

## Differences from Direct Docker MCP Servers

| Aspect | Docker MCP Gateway | Direct Docker MCP |
|--------|-------------------|-------------------|
| **Setup** | Via Docker Desktop UI | Manual configuration |
| **Management** | Centralized in Docker Desktop | Per-server config files |
| **Discovery** | Automatic from Catalog | Manual server addition |
| **Security** | Built-in resource limits | Manual container config |
| **OAuth** | Automatic handling | Manual token management |
| **Use Case** | Multiple servers, easy management | Single server, custom config |

## Related Files

- **OCR MCP Server**: `config/mcp-ocr-server.docker.json` (direct Docker config)
- **OSINT Tools MCP**: `config/osint-tools-mcp-server.docker.json` (direct Docker config)
- **MCP Docker Client**: `shared/modules/tools/mcp_docker_client.py` (dynamic image building)

## References

- [Docker MCP Toolkit Documentation](https://docs.docker.com/ai/mcp-catalog-and-toolkit/toolkit/)
- [Docker MCP Catalog](https://docs.docker.com/ai/mcp-catalog-and-toolkit/catalog/)
- [Dynamic MCP Feature](https://docs.docker.com/ai/mcp-catalog-and-toolkit/dynamic-mcp/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)


