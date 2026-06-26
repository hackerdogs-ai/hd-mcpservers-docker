<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Deepwebresearch MCP Server

MCP server wrapper for Deep Web Research — fetch and strip HTML from one or more URLs, returning clean extracted text for use in research and analysis workflows.

## What is Deep Web Research?

Deep Web Research is a purpose-built URL content fetcher that retrieves web pages via HTTPS, strips scripts, styles, and HTML tags, and returns clean readable text with metadata (status code, content type, text length). It supports single-URL and batch fetching (up to 20 URLs), with configurable character limits to prevent context overflow. No browser is required — it uses plain HTTP requests.

**No API keys required** — runs entirely inside the Docker container.

**Tools:**
- `fetch_url` — Fetch a single URL and return extracted text and HTTP metadata.
- `fetch_urls` — Fetch multiple URLs (comma- or newline-separated) and return extracted text for each.

## Tools Reference

### `fetch_url`

Fetch a single URL and return extracted text and metadata.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | — | URL to fetch |
| `max_chars` | integer | No | `50000` | Maximum characters to return (1000–500000) |

### `fetch_urls`

Fetch multiple URLs and return extracted text for each.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `urls` | string | Yes | — | Comma- or newline-separated list of URLs (max 20) |
| `max_chars_per_url` | integer | No | `20000` | Max characters per URL (1000–500000) |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Fetch the content of https://nvd.nist.gov/vuln/detail/CVE-2024-3094 and summarize the vulnerability."
- "Retrieve and compare the text from these three security advisories and identify common CVEs."
- "Fetch the blog post at this URL and extract the key technical findings."
- "Use the deep web research tool to pull text from a pastebin URL for analysis."
- "Fetch up to 10 links from this list and tell me which ones are reachable and what they contain."
- "Retrieve the content of a public threat intelligence report URL and summarize the IOCs mentioned."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/deepwebresearch-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8377:8377 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8377 \
  hackerdogs/deepwebresearch-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "deepwebresearch-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/deepwebresearch-mcp:latest"],
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
    "deepwebresearch-mcp": {
      "url": "http://localhost:8377/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8377` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/deepwebresearch-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name deepwebresearch-mcp-test -p 8377:8377 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/deepwebresearch-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8377/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8377/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8377/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_deepwebresearch","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop deepwebresearch-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Deepwebresearch CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint deepwebresearch hackerdogs/deepwebresearch-mcp:latest --help
```
