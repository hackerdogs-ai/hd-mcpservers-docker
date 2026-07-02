<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Shuffledns MCP Server

MCP server wrapper for [shuffledns](https://github.com/projectdiscovery/shuffledns) — high-speed subdomain enumeration and DNS resolution using massDNS.

## What is Shuffledns?

Shuffledns is a mass DNS resolver and subdomain brute-forcer by ProjectDiscovery, built on top of massDNS, capable of resolving millions of subdomains per second using custom wordlists. It filters wildcards, validates live subdomains, and supports input from stdin for pipeline integration with other recon tools. See [projectdiscovery/shuffledns](https://github.com/projectdiscovery/shuffledns) for full documentation.

**No API keys required** — shuffledns runs locally inside the Docker container.

**Summary.** MCP server wrapper for [shuffledns](https://github.com/projectdiscovery/shuffledns) — high-speed subdomain enumeration and DNS resolution using massDNS.

**Tools:**
- `run_shuffledns` — Run shuffledns with CLI arguments (e.g. example.com).

## Tools Reference

### `run_shuffledns`

Run shuffledns with CLI arguments (e.g. example.com).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | str | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `timeout_seconds` | int | No | `300` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "shuffledns output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use shuffledns to enumerate subdomains of example.com using the wordlist at /wordlists/subdomains.txt."
- "Run shuffledns on tesla.com and filter out wildcard DNS results."
- "Resolve a list of subdomains from subdomains.txt against example.com using shuffledns."
- "Use shuffledns to find live subdomains of target.org and save results to output.txt."
- "Pipe a list of potential subdomains into shuffledns and resolve which ones are active."
- "Run shuffledns with a custom resolver list to enumerate subdomains of example.com."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/shuffledns-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8393:8393 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8393 \
  hackerdogs/shuffledns-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "shuffledns-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/shuffledns-mcp:latest"],
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
    "shuffledns-mcp": {
      "url": "http://localhost:8393/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.


## Securely Accessing MCP

When running through the [Hackerdogs MCP Farm](https://hackerdogs.ai), servers are accessed through the authenticated gateway instead of direct container ports:

```json
{
  "mcpServers": {
    "shuffledns-mcp": {
      "url": "http://localhost:8485/shuffledns-mcp/mcp",
      "headers": {
        "Authorization": "Bearer <your-api-key>"
      }
    }
  }
}
```

> **Farm access:** The MCP Farm gateway handles authentication, rate limiting, and routing. Replace `localhost:8485` with your farm's host address and use your API key from the farm admin panel. See [Hackerdogs](https://hackerdogs.ai) for details.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8393` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/shuffledns-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name shuffledns-mcp-test -p 8393:8393 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/shuffledns-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8393/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8393/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8393/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_shuffledns","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop shuffledns-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Shuffledns CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint shuffledns hackerdogs/shuffledns-mcp:latest --help
```
