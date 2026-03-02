<p align="center">
  <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="200"/>
</p>

# OpenRisk MCP Server

MCP server wrapper for [OpenRisk](https://github.com/projectdiscovery/openrisk) — generates risk scores from Nuclei scan output using OpenAI GPT-4o for intelligent vulnerability risk assessment.

## What is OpenRisk?

OpenRisk is a risk scoring tool by ProjectDiscovery that analyzes Nuclei scan results and generates risk assessments using OpenAI's GPT-4o. It takes vulnerability scan output and produces risk scores with actionable recommendations.

## Prerequisites

OpenRisk requires a valid **OpenAI API key** to function. The tool uses GPT-4o to analyze Nuclei scan results and produce risk scores.

Get your key at: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

```bash
export OPENAI_API_KEY=sk-...
```

## Tools Reference

### `analyze_risk`

Analyze Nuclei scan results and generate a risk score using OpenAI GPT-4o. Requires `OPENAI_API_KEY`.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `scan_results` | string | Yes | — | Nuclei scan results content (text, markdown, or JSONL) |

<details>
<summary>Example response</summary>

```json
{
  "success": true,
  "output": "Risk Score: 7.5/10\n\nFindings:\n- Critical: SQL injection in /api/login\n- High: XSS in search parameter\n\nRecommendations:\n- Parameterize all SQL queries\n- Sanitize user input"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Analyze these Nuclei scan results and give me a risk score: [paste scan output]."
- "I ran a Nuclei scan on our staging environment. Here are the findings — what's the overall risk level and what should I fix first?"
- "Rate the risk of these vulnerability findings and provide prioritized remediation steps."
- "Take this Nuclei JSONL output and generate an executive risk summary."
- "Here's a Nuclei scan that found an SQL injection and two XSS issues — how severe is this and what's the risk?"
- "Analyze the attached scan results and tell me which findings are most critical for our production environment."

## Deploy

### Docker Compose (recommended)

```bash
OPENAI_API_KEY=sk-... docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e OPENAI_API_KEY=sk-... \
  hackerdogs/openrisk-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8115:8115 \
  -e OPENAI_API_KEY=sk-... \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8115 \
  hackerdogs/openrisk-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "openrisk-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "OPENAI_API_KEY",
        "hackerdogs/openrisk-mcp:latest"
      ],
      "env": {
        "OPENAI_API_KEY": "<your-openai-api-key>"
      }
    }
  }
}
```

### HTTP mode (streamable-http)

First, start the server using Docker Compose or `docker run` with HTTP mode (see [Deploy](#deploy) above) — API keys are passed as environment variables at container start time. Then point your MCP client at the running server:

```json
{
  "mcpServers": {
    "openrisk-mcp": {
      "url": "http://localhost:8115/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | **Required.** OpenAI API key for GPT-4o risk analysis |
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8115` | Port for streamable-http transport |

## Build

```bash
docker build -t hackerdogs/openrisk-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name openrisk-test -p 8115:8115 \
  -e MCP_TRANSPORT=streamable-http \
  -e OPENAI_API_KEY=sk-... \
  hackerdogs/openrisk-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8115/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8115/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8115/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"analyze_risk","arguments":{"scan_results":"[critical] SQL Injection at /api/login\n[high] XSS in search parameter"}}}'
```

**4. Clean up:**

```bash
docker stop openrisk-test
```
