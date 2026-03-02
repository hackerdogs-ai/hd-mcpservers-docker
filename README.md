<p align="center">
  <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="200"/>
</p>

# hd-mcpservers-docker

Registry of containerized MCP servers for security tools, ready for deployment on [Hackerdogs](https://hackerdogs.ai).

Each tool is wrapped as a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server using [FastMCP](https://github.com/jlowin/fastmcp), supporting both **stdio** and **HTTP streamable** transports. All tools are packaged as multi-architecture Docker images (linux/amd64, linux/arm64).

## Tool Registry

| # | Tool | Source | Description | Port | Image |
|---|------|--------|-------------|------|-------|
| 1 | [julius-mcp](./julius-mcp/) | [praetorian-inc/julius](https://github.com/praetorian-inc/julius) | LLM service fingerprinting | 8100 | `hackerdogs/julius-mcp` |
| 2 | [augustus-mcp](./augustus-mcp/) | [praetorian-inc/augustus](https://github.com/praetorian-inc/augustus) | LLM adversarial vulnerability testing | 8101 | `hackerdogs/augustus-mcp` |
| 3 | [brutus-mcp](./brutus-mcp/) | [praetorian-inc/brutus](https://github.com/praetorian-inc/brutus) | Multi-protocol credential testing | 8102 | `hackerdogs/brutus-mcp` |
| 4 | [titus-mcp](./titus-mcp/) | [praetorian-inc/titus](https://github.com/praetorian-inc/titus) | Secrets scanning (code, files, git) | 8103 | `hackerdogs/titus-mcp` |
| 5 | [nerva-mcp](./nerva-mcp/) | [praetorian-inc/nerva](https://github.com/praetorian-inc/nerva) | Network service fingerprinting | 8104 | `hackerdogs/nerva-mcp` |
| 6 | [naabu-mcp](./naabu-mcp/) | [projectdiscovery/naabu](https://github.com/projectdiscovery/naabu) | Fast port scanning | 8105 | `hackerdogs/naabu-mcp` |
| 7 | [cvemap-mcp](./cvemap-mcp/) | [projectdiscovery/cvemap](https://github.com/projectdiscovery/cvemap) | CVE search and exploration | 8106 | `hackerdogs/cvemap-mcp` |
| 8 | [uncover-mcp](./uncover-mcp/) | [projectdiscovery/uncover](https://github.com/projectdiscovery/uncover) | Exposed host discovery (Shodan, Censys, FOFA) | 8107 | `hackerdogs/uncover-mcp` |
| 9 | [dnsx-mcp](./dnsx-mcp/) | [projectdiscovery/dnsx](https://github.com/projectdiscovery/dnsx) | DNS query toolkit | 8108 | `hackerdogs/dnsx-mcp` |
| 10 | [tlsx-mcp](./tlsx-mcp/) | [projectdiscovery/tlsx](https://github.com/projectdiscovery/tlsx) | TLS certificate scanning | 8109 | `hackerdogs/tlsx-mcp` |
| 11 | [asnmap-mcp](./asnmap-mcp/) | [projectdiscovery/asnmap](https://github.com/projectdiscovery/asnmap) | ASN-to-network mapping | 8110 | `hackerdogs/asnmap-mcp` |
| 12 | [cloudlist-mcp](./cloudlist-mcp/) | [projectdiscovery/cloudlist](https://github.com/projectdiscovery/cloudlist) | Cloud asset discovery | 8111 | `hackerdogs/cloudlist-mcp` |
| 13 | [urlfinder-mcp](./urlfinder-mcp/) | [projectdiscovery/urlfinder](https://github.com/projectdiscovery/urlfinder) | Passive URL discovery | 8112 | `hackerdogs/urlfinder-mcp` |
| 14 | [tldfinder-mcp](./tldfinder-mcp/) | [projectdiscovery/tldfinder](https://github.com/projectdiscovery/tldfinder) | Private TLD discovery | 8113 | `hackerdogs/tldfinder-mcp` |
| 15 | [wappalyzergo-mcp](./wappalyzergo-mcp/) | [projectdiscovery/wappalyzergo](https://github.com/projectdiscovery/wappalyzergo) | Web technology detection | 8114 | `hackerdogs/wappalyzergo-mcp` |
| 16 | [openrisk-mcp](./openrisk-mcp/) | [projectdiscovery/openrisk](https://github.com/projectdiscovery/openrisk) | Risk scoring from Nuclei output | 8115 | `hackerdogs/openrisk-mcp` |
| 17 | [vulnx-mcp](./vulnx-mcp/) | [projectdiscovery/cvemap](https://github.com/projectdiscovery/cvemap) (vulnx binary) | Vulnerability search and analysis | 8116 | `hackerdogs/vulnx-mcp` |

### Reserved Ports (do not use)

- 80 (HTTP)
- 8000-8010 (general app servers)
- 8501-8510 (Streamlit)
- 9000-9010 (monitoring)

## Quick Start

### Run All Services

```bash
docker compose up -d
```

### Run a Single Service

```bash
docker compose up -d julius-mcp
```

### Build All Images Locally

```bash
docker compose build
```

### Use with Claude Desktop / Cursor (stdio mode)

Each tool has a `mcpServer.json` file. Example for julius-mcp:

```json
{
  "mcpServers": {
    "julius-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/julius-mcp:latest"],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_TRANSPORT` | Transport protocol: `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (when using streamable-http) | per-tool (see table) |
| `OPENAI_API_KEY` | Required for openrisk-mcp only | — |

## Directory Structure

Each tool follows this structure:

```
<tool>-mcp/
├── Dockerfile              # Multi-stage Docker build
├── mcp_server.py           # FastMCP server wrapping the CLI tool
├── requirements.txt        # Python dependencies
├── publish_to_hackerdogs.sh # Build & publish script
├── mcpServer.json          # MCP client configuration
├── docker-compose.yml      # Standalone compose file
├── test.sh                 # Test script
├── README.md               # Tool-specific documentation
└── progress.md             # Implementation progress tracking
```

## Publishing

Each tool has a `publish_to_hackerdogs.sh` script:

```bash
cd julius-mcp
./publish_to_hackerdogs.sh --build                    # Build locally
./publish_to_hackerdogs.sh --publish hackerdogs       # Publish to Docker Hub
./publish_to_hackerdogs.sh --build --publish hackerdogs # Build and publish
./publish_to_hackerdogs.sh --help                     # Show help
```

## Testing

Each tool has a `test.sh` script:

```bash
cd julius-mcp
./test.sh
```

## License

See [LICENSE](./LICENSE) for details.
