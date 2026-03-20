<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# VictoriaLogs MCP Server

MCP server for log analysis with [LogsQL](https://docs.victoriametrics.com/victorialogs/logsql/) queries via [VictoriaLogs](https://victoriametrics.com/products/victorialogs/).

**Requires:** A running VictoriaLogs instance (default: `http://localhost:9428`).

**Tools:**
- `victorialogs_query` — Query VictoriaLogs using LogsQL
- `victorialogs_hits` — Get hit counts over time for a LogsQL query
- `victorialogs_stats` — Get statistics for a LogsQL query
- `victorialogs_field_names` — Get field names from logs matching a query

## Deploy

### Docker Compose
```bash
docker-compose up -d
```
Set `VICTORIALOGS_URL` in the environment or a `.env` file.

### Docker Run (stdio)
```bash
docker run -i --rm -e VICTORIALOGS_URL=http://host.docker.internal:9428 hackerdogs/victorialogs-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8527:8527 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8527 \
  -e VICTORIALOGS_URL=http://host.docker.internal:9428 \
  hackerdogs/victorialogs-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`; set `VICTORIALOGS_URL` in `env`.  
**HTTP:** Connect to `http://localhost:8527` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8527` |
| `VICTORIALOGS_URL` | VictoriaLogs API URL | `http://localhost:9428` |

## Example prompts

- "Query VictoriaLogs for all error logs in the last hour."
- "Get hit counts for 'status:500' over 15-minute buckets."
- "Show field names for logs matching 'service:nginx'."
