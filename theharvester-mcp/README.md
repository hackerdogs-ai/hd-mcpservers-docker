<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# theHarvester MCP Server

MCP server wrapper for [Theharvester](https://github.com/laramies/theHarvester) — Email and subdomain harvesting from multiple sources.

## What is Theharvester?

Theharvester (theHarvester) is a security tool that provides: **Email and subdomain harvesting from multiple sources.**

See [laramies/theHarvester](https://github.com/laramies/theHarvester) for full documentation.

**No API keys required** — Theharvester runs locally inside the Docker container.

**Summary.** MCP server wrapper for [Theharvester](https://github.com/laramies/theHarvester) — Email and subdomain harvesting from multiple sources.

**Tools:**
- `run_theharvester` — Run theHarvester with the given arguments. Returns structured JSON output.


## Tools Reference

### `run_theharvester`

Run theHarvester with the given arguments. Returns structured JSON output.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `timeout_seconds` | integer | No | `600` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "theHarvester output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use theHarvester to gather emails and subdomains for example.com using all sources."
- "Run theHarvester with -d target.com -b google to harvest from Google."
- "Find all email addresses associated with company.com using theHarvester."
- "Use theHarvester to enumerate subdomains for target.org with -b crtsh."
- "Show me all available theHarvester data sources with --help."
- "Run theHarvester against example.com and output results in JSON format."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/theharvester-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8204:8204 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8204 \
  hackerdogs/theharvester-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "theharvester-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "MCP_TRANSPORT",
        "hackerdogs/theharvester-mcp:latest"
      ],
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
    "theharvester-mcp": {
      "url": "http://localhost:8204/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8204` | HTTP port (only used with `streamable-http`) |
| `THEHARVESTER_BIN` | `theHarvester` | Path or name of the theHarvester binary |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "nuclei", "naabu", "julius").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use naabu to scan example.com"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/theharvester-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name theharvester-mcp-test -p 8204:8204 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/theharvester-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8204/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8204/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8204/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_theharvester","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop theharvester-mcp-test
```


## Running the tool directly (bypassing MCP)

You can run the theHarvester CLI in the same container by overriding the entrypoint to gather emails/subdomains without starting the MCP server.

**Collect for domain:**

```bash
docker run -i --rm --entrypoint theHarvester hackerdogs/theharvester-mcp:latest -d example.com -b all
```

**Show help:**

```bash
docker run -i --rm --entrypoint theHarvester hackerdogs/theharvester-mcp:latest -h
```