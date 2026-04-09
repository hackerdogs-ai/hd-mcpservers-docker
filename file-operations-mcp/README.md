<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# File Operations MCP Server

MCP server for file format conversion and analysis — CSV, JSON, Excel.

**Tools:**
- `convert_csv_to_json` — Convert CSV file to JSON
- `convert_json_to_csv` — Convert JSON file to CSV
- `file_info` — Get file information (size, type, modification time)

## Deploy

### Docker Compose
```bash
docker-compose up -d
```

### Docker Run (stdio)
```bash
docker run -i --rm hackerdogs/file-operations-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8522:8522 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8522 \
  hackerdogs/file-operations-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`.  
**HTTP:** Connect to `http://localhost:8522` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8522` |

## Example prompts

- "Convert data.csv to JSON format."
- "Get file info for /tmp/report.csv."
- "Convert results.json to a CSV file."
