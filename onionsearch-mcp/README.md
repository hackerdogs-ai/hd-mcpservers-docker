<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# OnionSearch MCP Server

MCP server wrapper for [OnionSearch](https://github.com/megadose/OnionSearch) — Dark Web .onion search engine scraper.

## What is OnionSearch?

OnionSearch (onionsearch) is a security tool that provides: **Dark Web search capabilities by scraping URLs from multiple .onion search engines (ahmia, tor66, phobos, deeplink, and 12+ more) via the Tor network.**

See [megadose/OnionSearch](https://github.com/megadose/OnionSearch) for full documentation.

**Tor proxy required** — OnionSearch needs a Tor SOCKS5 proxy to access .onion sites. Set `TOR_PROXY` to point at your Tor proxy (see `docker-compose.tor.yml` for a ready-to-use proxy container).

**Summary.** MCP server wrapper for [OnionSearch](https://github.com/megadose/OnionSearch) — Dark Web .onion search engine scraper.

**Tools:**
- `run_onionsearch` — Run onionsearch with the given arguments. Returns raw CLI output.
- `onionsearch_search` — Structured Dark Web search with parsed JSON results.


## Tools Reference

### `run_onionsearch`

Run onionsearch with the given arguments. Returns raw CLI output. The `TOR_PROXY` environment variable is automatically injected as `--proxy` unless you explicitly include it.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `'"search term" --limit 3'`) |
| `timeout_seconds` | integer | No | `300` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```
Searching on ahmia...
Searching on tor66...
Results written to /tmp/onionsearch_output.csv
```

</details>

### `onionsearch_search`

Structured Dark Web search. Builds the OnionSearch command, runs it, and returns parsed JSON results.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | — | Search query string |
| `engines` | string | No | `""` | Space-separated engine names (e.g. `"ahmia tor66 phobos"`) |
| `exclude` | string | No | `""` | Space-separated engines to exclude |
| `limit` | integer | No | `3` | Max pages per engine to scrape |
| `timeout_seconds` | integer | No | `300` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "query": "example",
  "results_count": 15,
  "results": [
    {
      "engine": "ahmia",
      "name": "Example Onion Site",
      "url": "http://example.onion"
    }
  ]
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Search the Dark Web for 'leaked credentials' using OnionSearch."
- "Use onionsearch to find .onion URLs related to 'marketplace'."
- "Search only ahmia and tor66 engines for 'cybersecurity tools' on the Dark Web."
- "Run OnionSearch for 'forum' with a limit of 5 pages per engine."
- "Show me all available OnionSearch options with --help."
- "Search the Dark Web for 'ransomware' excluding notevil and candle engines."

## Deploy

### Docker Compose (recommended)

First start the Tor proxy, then the MCP server:

```bash
docker-compose -f docker-compose.tor.yml up -d
docker-compose up -d
```

Or run both together:

```bash
docker-compose -f docker-compose.yml -f docker-compose.tor.yml up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm -e TOR_PROXY=127.0.0.1:9050 hackerdogs/onionsearch-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8372:8372 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8372 \
  -e TOR_PROXY=127.0.0.1:9050 \
  hackerdogs/onionsearch-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "onionsearch-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "TOR_PROXY", "hackerdogs/onionsearch-mcp:latest"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "TOR_PROXY": "127.0.0.1:9050"
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
    "onionsearch-mcp": {
      "url": "http://localhost:8372/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8372` | HTTP port (only used with `streamable-http`) |
| `TOR_PROXY` | `127.0.0.1:9050` | Tor SOCKS5 proxy address (host:port) |
| `ONIONSEARCH_BIN` | `onionsearch` | Path or name of the OnionSearch binary |

## Tor Proxy Setup

OnionSearch requires a Tor SOCKS5 proxy. A ready-to-use `docker-compose.tor.yml` is included:

```bash
docker-compose -f docker-compose.tor.yml up -d
```

This starts a Tor SOCKS5 proxy on port 9050. Set `TOR_PROXY=tor-proxy:9050` (Docker network) or `TOR_PROXY=127.0.0.1:9050` (host) to connect.

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "nuclei", "naabu", "julius").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use OnionSearch to find .onion URLs for 'marketplace'"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/onionsearch-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name onionsearch-mcp-test -p 8372:8372 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/onionsearch-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8372/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8372/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8372/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_onionsearch","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop onionsearch-mcp-test
```


## Running the tool directly (bypassing MCP)

You can run OnionSearch directly in the same container by overriding the entrypoint to search the Dark Web without starting the MCP server.

**Show help:**

```bash
docker run --rm --entrypoint onionsearch hackerdogs/onionsearch-mcp:latest --help
```

**Search with Tor proxy:**

```bash
docker run --rm --entrypoint onionsearch hackerdogs/onionsearch-mcp:latest "search term" --proxy 127.0.0.1:9050 --limit 3
```

**Search specific engines:**

```bash
docker run --rm --entrypoint onionsearch hackerdogs/onionsearch-mcp:latest "query" --proxy 127.0.0.1:9050 --engines ahmia tor66 phobos
```
