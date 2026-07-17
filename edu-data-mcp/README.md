<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Edu Data MCP Server

MCP server wrapper for [edu-data-mcp-server](https://github.com/ousepachn/edu-data-mcp-server) — query the Urban Institute's Education Data API for K–12 and postsecondary education statistics across the United States.

## What is Edu Data MCP Server?

The Edu Data MCP server provides access to the Urban Institute's Education Data Portal API, which aggregates data from NCES, IPEDS, CCD, and other federal education datasets. It enables AI assistants to query school-level enrollment figures, graduation rates, test scores, finance data, and postsecondary institution characteristics across public and private schools in the US. See [ousepachn/edu-data-mcp-server](https://github.com/ousepachn/edu-data-mcp-server) for full documentation.

**No API keys required** — queries the public Urban Institute Education Data API.

**Tools:**
- `edu_data_info` — Return status information for the connected Edu Data MCP server.

## Tools Reference

### `edu_data_info`

Return basic status for the Edu Data MCP server.

_No parameters._

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Query the Urban Institute Education Data API for graduation rates at public high schools in Texas in 2022."
- "Retrieve IPEDS enrollment data for all four-year public universities in California."
- "Fetch CCD data on per-pupil expenditure for school districts in New York State."
- "Find postsecondary institutions with the highest STEM degree conferral rates using IPEDS data."
- "Query education data for free and reduced-price lunch eligibility rates across school districts in 2023."
- "Use edu-data to compare math proficiency test scores across states using NAEP data."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/edu-data-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8416:8416 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8416 \
  hackerdogs/edu-data-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "edu-data-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/edu-data-mcp:latest"],
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
    "edu-data-mcp": {
      "url": "http://localhost:8416/mcp"
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
    "edu-data-mcp": {
      "url": "http://localhost:8485/edu-data-mcp/mcp",
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
| `MCP_PORT` | `8416` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/edu-data-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name edu-data-mcp-test -p 8416:8416 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/edu-data-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8416/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8416/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8416/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_edu_data","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop edu-data-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Edu Data CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint edu-data hackerdogs/edu-data-mcp:latest --help
```
