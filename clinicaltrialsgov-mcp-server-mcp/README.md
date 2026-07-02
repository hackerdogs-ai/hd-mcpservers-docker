<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# ClinicalTrials.gov MCP Server

MCP server wrapper for [ClinicalTrials.gov](https://github.com/pauljunsukhan/clinicaltrialsgov-mcp) — search the NLM's global registry of clinical studies by condition, intervention, location, and status.

## What is ClinicalTrials.gov?

ClinicalTrials.gov is the U.S. National Library of Medicine's registry of publicly and privately supported clinical studies conducted around the world. This MCP server wraps the `clinicaltrialsgov-mcp-server` package, enabling structured searches of the ClinicalTrials.gov API by condition, intervention, location, sponsor, phase, and enrollment status — and retrieval of full study details, eligibility criteria, and reported results. See [github.com/pauljunsukhan/clinicaltrialsgov-mcp](https://github.com/pauljunsukhan/clinicaltrialsgov-mcp) for full documentation.

**No API keys required** — queries the public ClinicalTrials.gov API directly.

## Tools Reference

| Tool | Description |
|------|-------------|
| `clinicaltrials_analyze_trends` | Clinicaltrials Analyze Trends |
| `clinicaltrials_compare_studies` | Clinicaltrials Compare Studies |
| `clinicaltrials_find_eligible_studies` | Clinicaltrials Find Eligible Studies |
| `clinicaltrials_get_study` | Clinicaltrials Get Study |
| `clinicaltrials_search_studies` | Clinicaltrials Search Studies |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Search ClinicalTrials.gov for active Phase 3 trials studying semaglutide for obesity."
- "Find clinical trials recruiting participants in New York for Alzheimer's disease."
- "Look up the eligibility criteria and study design for trial NCT04280705."
- "Search for completed trials that studied the combination of immunotherapy and chemotherapy for lung cancer."
- "Find all trials sponsored by NIH for Type 1 Diabetes published in the last two years."
- "What are the reported outcomes of the RECOVERY trial for COVID-19 treatments?"

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/clinicaltrialsgov-mcp-server-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8632:8632 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8632 \
  hackerdogs/clinicaltrialsgov-mcp-server-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "clinicaltrialsgov-mcp-server-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "hackerdogs/clinicaltrialsgov-mcp-server-mcp:latest"
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
    "clinicaltrialsgov-mcp-server-mcp": {
      "url": "http://localhost:8632/mcp"
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
    "clinicaltrialsgov-mcp-server-mcp": {
      "url": "http://localhost:8485/clinicaltrialsgov-mcp-server-mcp/mcp",
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
| `MCP_PORT` | `8632` | HTTP port (only used with `streamable-http`) |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name.
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly. If you don't specify, Hackerdogs will automatically choose the best tool for the job.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/clinicaltrialsgov-mcp-server-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name clinicaltrialsgov-mcp-server-mcp-test -p 8632:8632 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/clinicaltrialsgov-mcp-server-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8632/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8632/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8632/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop clinicaltrialsgov-mcp-server-mcp-test
```
