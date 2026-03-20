<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# Graphviz DOT MCP Server

MCP server for [Graphviz](https://graphviz.org) — render DOT diagrams to SVG or PNG.

**Tools:**
- `render_dot` — Render a Graphviz DOT diagram to SVG or PNG format

## Deploy

### Docker Compose
```bash
docker-compose up -d
```

### Docker Run (stdio)
```bash
docker run -i --rm hackerdogs/graphviz-dot-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8523:8523 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8523 \
  hackerdogs/graphviz-dot-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`.
**HTTP:** Connect to `http://localhost:8523` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8523` |

## Example prompts

- "Render this DOT diagram: digraph { A -> B -> C }"
- "Create an SVG from this Graphviz DOT source."
