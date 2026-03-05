<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Uncover MCP Server

MCP server wrapper for [Uncover](https://github.com/projectdiscovery/uncover) — discovers exposed hosts via internet search APIs including Shodan, Censys, FOFA, Hunter, Quake, ZoomEye, Netlas, and CriminalIP.

## What is Uncover?

Uncover is a host discovery tool by ProjectDiscovery that queries multiple internet search engines (Shodan, Censys, FOFA, Hunter, Quake, ZoomEye, Netlas, CriminalIP) to find exposed hosts and services. It provides a unified interface across all supported engines.

## Prerequisites

Uncover supports multiple search engines, each with its own API key. All keys are optional — the `shodan-idb` engine works **without any API key**.

| Engine | Environment Variable(s) | Get Key |
|--------|------------------------|---------|
| Shodan | `SHODAN_API_KEY` | [account.shodan.io](https://account.shodan.io) |
| Shodan-IDB | None needed | — |
| Censys | `CENSYS_API_ID` + `CENSYS_API_SECRET` | [search.censys.io/account/api](https://search.censys.io/account/api) |
| FOFA | `FOFA_EMAIL` + `FOFA_KEY` | [en.fofa.info](https://en.fofa.info) |
| Hunter | `HUNTER_API_KEY` | [hunter.how](https://hunter.how) |
| Quake | `QUAKE_TOKEN` | [quake.360.net](https://quake.360.net) |
| ZoomEye | `ZOOMEYE_API_KEY` | [zoomeye.org](https://www.zoomeye.org) |
| Netlas | `NETLAS_API_KEY` | [netlas.io](https://netlas.io) |
| CriminalIP | `CRIMINALIP_API_KEY` | [criminalip.io](https://www.criminalip.io) |

**Summary.** MCP server wrapper for [Uncover](https://github.com/projectdiscovery/uncover) — discovers exposed hosts via internet search APIs including Shodan, Censys, FOFA, Hunter, Quake, ZoomEye, Netlas, and CriminalIP.

**Tools:**
- `search_hosts` — Search for exposed hosts using internet search engines (Shodan, Censys, FOFA, etc.).


## Tools Reference

### `search_hosts`

Search for exposed hosts using internet search engines (Shodan, Censys, FOFA, etc.).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | — | Search query (e.g. `"nginx"`, `"Apache port:443"`, `"org:Google"`) |
| `engines` | string | No | `"shodan-idb"` | Comma-separated engines: `shodan`, `shodan-idb`, `censys`, `fofa`, `hunter`, `quake`, `zoomeye`, `netlas`, `criminalip` |
| `fields` | string | No | `"ip,port,host"` | Comma-separated output fields |
| `limit` | integer | No | `100` | Max results to return |
| `json_output` | boolean | No | `true` | Return results in JSON format |

<details>
<summary>Example response</summary>

```json
{
  "success": true,
  "output": [{"ip": "93.184.216.34", "port": 443, "host": "example.com"}]
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Find exposed Apache servers on the internet using Shodan."
- "Search for hosts running Elasticsearch on port 9200 that are publicly accessible."
- "Look up all exposed assets belonging to the organization 'Tesla' using shodan-idb."
- "Find internet-facing Redis instances with no authentication."
- "Search Censys for hosts with 'nginx' on port 443 and show me the IPs and hostnames."
- "Find exposed Kubernetes API servers (port 6443) on the public internet."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e SHODAN_API_KEY=your_key \
  hackerdogs/uncover-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8107:8107 \
  -e SHODAN_API_KEY=your_key \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8107 \
  hackerdogs/uncover-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "uncover-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "SHODAN_API_KEY",
        "-e", "CENSYS_API_ID",
        "-e", "CENSYS_API_SECRET",
        "-e", "FOFA_EMAIL",
        "-e", "FOFA_KEY",
        "-e", "HUNTER_API_KEY",
        "-e", "QUAKE_TOKEN",
        "-e", "ZOOMEYE_API_KEY",
        "-e", "NETLAS_API_KEY",
        "-e", "CRIMINALIP_API_KEY",
        "-e", "MCP_TRANSPORT",
        "hackerdogs/uncover-mcp:latest"
      ],
      "env": {
        "SHODAN_API_KEY": "<your-shodan-api-key>",
        "CENSYS_API_ID": "<your-censys-api-id>",
        "CENSYS_API_SECRET": "<your-censys-api-secret>",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

### HTTP mode (streamable-http)

First, start the server using Docker Compose or `docker run` with HTTP mode (see [Deploy](#deploy) above) — API keys are passed as environment variables at container start time. Then point your MCP client at the running server:

```json
{
  "mcpServers": {
    "uncover-mcp": {
      "url": "http://localhost:8107/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SHODAN_API_KEY` | — | Shodan API key |
| `CENSYS_API_ID` | — | Censys API ID |
| `CENSYS_API_SECRET` | — | Censys API secret |
| `FOFA_EMAIL` | — | FOFA account email |
| `FOFA_KEY` | — | FOFA API key |
| `HUNTER_API_KEY` | — | Hunter API key |
| `QUAKE_TOKEN` | — | Quake 360 API token |
| `ZOOMEYE_API_KEY` | — | ZoomEye API key |
| `NETLAS_API_KEY` | — | Netlas API key |
| `CRIMINALIP_API_KEY` | — | CriminalIP API key |
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8107` | Port for streamable-http transport |

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
docker build -t hackerdogs/uncover-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name uncover-test -p 8107:8107 \
  -e MCP_TRANSPORT=streamable-http \
  -e SHODAN_API_KEY=your_key \
  hackerdogs/uncover-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8107/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8107/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8107/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_hosts","arguments":{"query":"nginx","engines":"shodan-idb","limit":10}}}'
```

**4. Clean up:**

```bash
docker stop uncover-test
```
