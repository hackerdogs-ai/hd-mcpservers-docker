<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Assetfinder MCP Server

MCP server wrapper for [Assetfinder](https://github.com/tomnomnom/assetfinder) — passive subdomain enumeration by querying certificate transparency logs, DNS datasets, and web scraping sources.

## What is Assetfinder?

Assetfinder is a passive reconnaissance tool by tomnomnom that discovers subdomains and related domains without sending packets to the target. It queries sources such as Facebook's certificate transparency API, crt.sh, HackerTarget, VirusTotal, and several others to surface domains you might not find through direct probing. See [tomnomnom/assetfinder](https://github.com/tomnomnom/assetfinder) for full documentation.

**No API keys required** — Assetfinder runs locally inside the Docker container using public data sources.

**Summary.** MCP server wrapper for [Assetfinder](https://github.com/tomnomnom/assetfinder) — passive subdomain and related-domain discovery via certificate transparency and public DNS datasets.

**Tools:**
- `run_assetfinder` — Run assetfinder with CLI arguments (e.g. example.com).

## Tools Reference

### `run_assetfinder`

Run assetfinder with CLI arguments (e.g. example.com).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | str | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `timeout_seconds` | int | No | `300` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "assetfinder output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use assetfinder to find all subdomains of example.com."
- "Run assetfinder against tesla.com and list every subdomain discovered."
- "Find related domains and subdomains for hackerone.com using assetfinder."
- "Enumerate subdomains of target.com with assetfinder and filter out wildcard results."
- "Run assetfinder on bugcrowd.com to support my reconnaissance before a bug bounty engagement."
- "Use assetfinder to discover subdomains of shopify.com and count how many unique results are returned."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/assetfinder-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8384:8384 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8384 \
  hackerdogs/assetfinder-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "assetfinder-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/assetfinder-mcp:latest"],
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
    "assetfinder-mcp": {
      "url": "http://localhost:8384/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8384` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/assetfinder-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name assetfinder-mcp-test -p 8384:8384 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/assetfinder-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8384/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8384/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8384/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_assetfinder","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop assetfinder-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Assetfinder CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint assetfinder hackerdogs/assetfinder-mcp:latest --help
```
