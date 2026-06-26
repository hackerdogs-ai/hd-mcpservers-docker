<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# PubMed MCP Server

MCP server wrapper for [PubMed MCP](https://github.com/YUZongmin/pubmed-mcp-server) — search and analyze biomedical literature from the NCBI PubMed database.

## What is PubMed?

PubMed MCP Server enables AI assistants to search over 36 million citations in the NCBI PubMed database — covering biomedical literature, clinical trials, and life science research. It supports keyword search, MeSH term filtering, date range and author filters, abstract retrieval, and citation fetching, making it a powerful tool for systematic literature reviews and evidence-based research. See [YUZongmin/pubmed-mcp-server](https://github.com/YUZongmin/pubmed-mcp-server) for full documentation.

**No API keys required** — PubMed MCP uses the free NCBI Entrez API, which runs without authentication at moderate rate limits.

**Tools:**
- `pubmed_info` — Return basic info / status for PubMed MCP.

## Tools Reference

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Search PubMed for randomized controlled trials on metformin and cardiovascular outcomes published since 2020."
- "Find the top 10 most cited papers on CRISPR-Cas9 gene editing from 2015 to 2023."
- "Search PubMed for systematic reviews on mRNA vaccines and retrieve their abstracts."
- "Find papers by the author 'Smith JA' on colorectal cancer published in journals indexed by PubMed."
- "What does the recent PubMed literature say about long COVID neurological symptoms?"
- "Search for clinical trials on checkpoint inhibitors in non-small cell lung cancer and summarize the outcomes."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/pubmed-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8446:8446 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8446 \
  hackerdogs/pubmed-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "pubmed-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/pubmed-mcp:latest"],
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
    "pubmed-mcp": {
      "url": "http://localhost:8446/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8446` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/pubmed-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name pubmed-mcp-test -p 8446:8446 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/pubmed-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8446/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8446/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8446/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"pubmed_info","arguments":{}}}'
```

**4. Clean up:**

```bash
docker stop pubmed-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the PubMed MCP server in the same container by overriding the entrypoint without starting the MCP wrapper.

**Show help:**

```bash
docker run -i --rm --entrypoint python hackerdogs/pubmed-mcp:latest mcp_server.py --help
```
