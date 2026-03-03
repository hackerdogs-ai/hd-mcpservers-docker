<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Titus MCP Server

MCP server wrapper for [Titus](https://github.com/praetorian-inc/titus) — secret detection tool by Praetorian that scans source code, files, and git history for leaked credentials.

## What is Titus?

Titus scans source code, files, and git history for leaked API keys, tokens, credentials, and other secrets using **459 detection rules**. It supports scanning local directories as well as full git commit history to find secrets that may have been committed and later removed.

**No API keys required** — Titus runs entirely locally against your files and repositories.

## Tools Reference

### `scan_path`

Scan files and directories for secrets (API keys, tokens, credentials) using 459 detection rules.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | string | Yes | — | File or directory path to scan |
| `validate` | boolean | No | `false` | Validate discovered secrets against live services |
| `output_format` | string | No | `"json"` | Output format: `"json"` or `"csv"` |
| `rules_include` | string | No | `""` | Rule IDs or tags to include (empty = all) |
| `rules_exclude` | string | No | `""` | Rule IDs or tags to exclude |

<details>
<summary>Example response</summary>

```json
{
  "success": true,
  "output": [
    {"rule_id": "aws-access-key", "file": "config.py", "line": 42, "match": "AKIA...XXXX", "severity": "high"}
  ]
}
```

</details>

### `scan_git`

Scan git history for secrets leaked in past commits.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | string | Yes | — | Path to a git repository |
| `validate` | boolean | No | `false` | Validate discovered secrets |
| `output_format` | string | No | `"json"` | Output format: `"json"` or `"csv"` |
| `rules_include` | string | No | `""` | Rule IDs or tags to include |
| `rules_exclude` | string | No | `""` | Rule IDs or tags to exclude |

### `list_rules`

List all 459 available secret detection rules. _No parameters._

### `generate_report`

Generate a report from the most recent scan.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `output_format` | string | No | `"json"` | Output format: `"json"` or `"csv"` |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Scan the /app/project directory for any leaked API keys, tokens, or secrets."
- "Check the git history of /app/repo for any secrets that were committed and later removed."
- "Scan /app/code but only look for AWS-related secrets like access keys and secret keys."
- "List all the secret detection rules that Titus supports."
- "Scan /app/config and validate any discovered secrets against live services to check if they're still active."
- "Generate a report from the last scan in CSV format."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/titus-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8103:8103 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8103 \
  hackerdogs/titus-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "titus-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/titus-mcp:latest"],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

### HTTP mode (streamable-http)

First, start the server using Docker Compose or `docker run` with HTTP mode (see [Deploy](#deploy) above), then point your MCP client at the running server:

```json
{
  "mcpServers": {
    "titus-mcp": {
      "url": "http://localhost:8103/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8103` | HTTP port (only used with `streamable-http`) |

## Build

```bash
docker build -t hackerdogs/titus-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name titus-test -p 8103:8103 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/titus-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8103/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8103/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8103/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_rules","arguments":{}}}'
```

**4. Clean up:**

```bash
docker stop titus-test
```
