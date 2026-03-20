<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# Cloud Datacenter MCP Server

MCP server to identify if IPs belong to **AWS**, **Azure**, **GCP**, **Cloudflare**, or other cloud providers by checking live IP range feeds.

**Tools:**
- `cloud_lookup_ip` — Check if an IP belongs to a known cloud provider

## Deploy

### Docker Compose
```bash
docker-compose up -d
```

### Docker Run (stdio)
```bash
docker run -i --rm hackerdogs/cloud-datacenter-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8520:8520 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8520 \
  hackerdogs/cloud-datacenter-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`.  
**HTTP:** Connect to `http://localhost:8520` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8520` |

## Example prompts

- "Is 52.94.76.1 an AWS IP?"
- "Check if 1.1.1.1 belongs to a cloud provider."
- "What cloud provider owns 35.190.247.1?"
