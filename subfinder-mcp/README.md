<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Subfinder MCP Server

MCP server wrapper for [subfinder](https://github.com/projectdiscovery/subfinder) — passive subdomain enumeration.

## What is Subfinder?

Subfinder is a fast passive subdomain enumeration tool by [ProjectDiscovery](https://github.com/projectdiscovery/subfinder). It discovers subdomains for a target domain by querying multiple public and private data sources (certificate transparency logs, search engines, DNS datasets, etc.) without performing active scanning.

See [projectdiscovery/subfinder](https://github.com/projectdiscovery/subfinder) for full documentation.

**No API keys required** — Subfinder runs locally inside the Docker container using free public sources. Optional API keys for premium sources can be configured via environment variables.

**Summary.** MCP server wrapper for [subfinder](https://github.com/projectdiscovery/subfinder) — passive subdomain enumeration using multiple public and private data sources.

**Tools:**
- `enumerate_subdomains` — Discover subdomains for a domain using passive sources. Returns structured JSON with subdomain list, count, and sources used.
- `run_subfinder` — Run subfinder with arbitrary CLI arguments for advanced usage.
- `list_subfinder_sources` — List all available passive enumeration data sources.


## Tools Reference

### `enumerate_subdomains`

Discover subdomains for a given domain using passive sources.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domain` | string | Yes | — | Target domain (e.g. `"example.com"`) |
| `timeout` | integer | No | `120` | Maximum enumeration time in seconds |
| `sources` | string | No | `""` | Comma-separated sources to use (e.g. `"crtsh,hackertarget"`) |
| `exclude_sources` | string | No | `""` | Comma-separated sources to exclude |
| `recursive` | boolean | No | `false` | Enable recursive subdomain discovery |
| `max_depth` | integer | No | `1` | Maximum recursion depth |
| `only_active` | boolean | No | `false` | Only return subdomains with active DNS records |
| `resolve` | boolean | No | `false` | Resolve discovered subdomains and include IPs |

<details>
<summary>Example response</summary>

```json
{
  "domain": "example.com",
  "subdomains": [
    "api.example.com",
    "blog.example.com",
    "dev.example.com",
    "mail.example.com",
    "www.example.com"
  ],
  "count": 5,
  "sources_used": ["crtsh", "hackertarget", "rapiddns"]
}
```

</details>

### `run_subfinder`

Run subfinder with arbitrary command-line arguments for advanced usage.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `"-d example.com -silent"`) |
| `timeout_seconds` | integer | No | `300` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "host": "api.example.com",
  "source": "crtsh",
  "input": "example.com"
}
```

</details>

### `list_subfinder_sources`

List all available passive enumeration data sources.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| *(none)* | — | — | — | No parameters required |

<details>
<summary>Example response</summary>

```json
{
  "sources": ["alienvault", "anubis", "bevigil", "binaryedge", "bufferover", "crtsh", ...],
  "count": 45
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Find all subdomains of example.com using subfinder."
- "Enumerate subdomains for tesla.com and show me only active ones."
- "Use subfinder to discover subdomains of hackerone.com using only crtsh and hackertarget sources."
- "Run recursive subdomain enumeration on example.com."
- "What data sources does subfinder support?"
- "Use subfinder to scan example.com and exclude waybackarchive source."
- "Find subdomains of example.com and resolve their IP addresses."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/subfinder-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8367:8367 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8367 \
  hackerdogs/subfinder-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "subfinder-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/subfinder-mcp:latest"],
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
    "subfinder-mcp": {
      "url": "http://localhost:8367/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8367` | HTTP port (only used with `streamable-http`) |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "subfinder").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use subfinder to enumerate subdomains for example.com"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/subfinder-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name subfinder-mcp-test -p 8367:8367 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/subfinder-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8367/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8367/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8367/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"enumerate_subdomains","arguments":{"domain":"example.com"}}}'
```

**4. Clean up:**

```bash
docker stop subfinder-mcp-test
```


## Running the tool directly (bypassing MCP)

You can run the subfinder CLI in the same container by overriding the entrypoint to enumerate subdomains without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint subfinder hackerdogs/subfinder-mcp:latest -h
```

**Quick enumeration:**

```bash
docker run -i --rm --entrypoint subfinder hackerdogs/subfinder-mcp:latest -d example.com -silent
```
