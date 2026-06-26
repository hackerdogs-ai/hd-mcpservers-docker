<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Baidusearch MCP Server

MCP server wrapper for Baidusearch — OSINT tool that queries Baidu's web index and extracts email addresses and hostnames from search results.

## What is Baidusearch?

Baidusearch is a custom OSINT (Open Source Intelligence) MCP tool that submits queries to Baidu and scrapes the resulting HTML to extract email addresses and hostnames. It pages through up to 10 result pages per query and returns a deduplicated, sorted list of discovered emails and the top 100 hostnames — making it useful for passive reconnaissance against domains and organizations with a strong Chinese-language or Asia-Pacific web presence.

**No API keys required** — the tool uses Baidu's public web interface and runs entirely inside the Docker container.

**Tools:**
- `baidu_search` — Search Baidu for a query and extract emails and hostnames from up to `limit` result pages.

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Search Baidu for 'site:example.com' and extract all email addresses found in the results."
- "Use baidusearch to find hostnames associated with 'targetcorp.com' in Baidu's index."
- "Run a Baidu search for '@targetdomain.com email' and list all discovered email addresses."
- "Search Baidu for 'filetype:pdf site:example.com' and extract hostnames from the results."
- "Use baidusearch to harvest subdomains of 'example.com' visible in Baidu's search results."
- "Query Baidu for 'contact example.com' with a limit of 5 pages and show extracted emails."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/baidusearch-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8514:8514 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8514 \
  hackerdogs/baidusearch-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "baidusearch-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/baidusearch-mcp:latest"],
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
    "baidusearch-mcp": {
      "url": "http://localhost:8514/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8514` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/baidusearch-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name baidusearch-mcp-test -p 8514:8514 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/baidusearch-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8514/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8514/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8514/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_baidusearch","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop baidusearch-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Baidusearch CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint baidusearch hackerdogs/baidusearch-mcp:latest --help
```
