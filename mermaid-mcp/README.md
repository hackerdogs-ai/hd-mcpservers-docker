<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# Mermaid MCP Server

MCP server for [Mermaid](https://mermaid.js.org) — render Mermaid diagrams to SVG or PNG.

**Tools:**
- `render_mermaid` — Render a Mermaid diagram to SVG or PNG format

## Deploy

### Docker Compose
```bash
docker-compose up -d
```

### Docker Run (stdio)
```bash
docker run -i --rm hackerdogs/mermaid-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8524:8524 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8524 \
  hackerdogs/mermaid-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`.
**HTTP:** Connect to `http://localhost:8524` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8524` |

## Example prompts

- "Render this Mermaid diagram: graph TD; A-->B-->C"
- "Create an SVG flowchart from Mermaid syntax."
