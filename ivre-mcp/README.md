<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# IVRE MCP Server

MCP server wrapper for [IVRE](https://github.com/ivre/ivre) — query an existing IVRE deployment for active scan results, passive reconnaissance, DNS records, and network flows.

## What is IVRE?

IVRE (Instrument de Veille sur les Réseaux Extérieurs) is an open-source network reconnaissance framework that stores and indexes the output of Nmap, Masscan, Zeek, and other tools into a database, then provides a powerful query interface to explore hosts, services, passive DNS, SSL certificates, and network flows. This MCP server connects to an existing IVRE Web API deployment to expose its query capabilities as tools. See [ivre/ivre](https://github.com/ivre/ivre) for full documentation.

**No API keys required** — connects to your own self-hosted IVRE instance via the `IVRE_WEB_URL` environment variable.

**Tools:**
- `query_hosts` — Query hosts from the IVRE scan or view database with filters.
- `count_hosts` — Count hosts matching a filter in the IVRE database.
- `query_passive` — Query passive reconnaissance records (DNS, HTTP headers, SSL certs, SSH keys).
- `count_passive` — Count passive reconnaissance records matching a filter.
- `top_values` — Get the most common values for a field (service, port, country, etc.).
- `distinct_values` — Get all distinct values for a field across the dataset.
- `get_host_ips` — Get a compact list of IP addresses matching a filter.
- `get_ips_ports` — Get IP addresses with their open ports.
- `get_timeline` — Get temporal distribution of scan results for time-series analysis.
- `ip_data` — Get geolocation and ASN data for a specific IP address.
- `passive_dns` — Query passive DNS records for a domain or IP.
- `query_flows` — Query aggregated network flow data from the IVRE flow database.

## Tools Reference

### `count_passive`

Count passive reconnaissance records matching a filter.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filter` | str | No | `""` | IVRE filter string for passive data. Leave empty to count all records. |

### `query_hosts`

Query hosts from the IVRE scan or view database.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `database` | str | No | `"view"` | Database to query: `"scans"` or `"view"` |
| `filter` | str | No | `""` | IVRE filter string (e.g. `"port:22"`, `"service:http"`, `"country:US"`) |
| `limit` | int | No | `50` | Maximum number of results |
| `skip` | int | No | `0` | Number of results to skip for pagination |
| `sort` | str | No | `""` | Sort field; prefix with `-` for descending |

### `query_passive`

Query passive reconnaissance records (DNS, HTTP headers, SSL certificates, SSH keys).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filter` | str | No | `""` | IVRE filter string for passive data |
| `limit` | int | No | `50` | Maximum number of results |
| `skip` | int | No | `0` | Number of results to skip |
| `sort` | str | No | `""` | Sort field |

### `ip_data`

Get geolocation and ASN data for a specific IP address.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `address` | str | Yes | — | IP address to look up (e.g. `"8.8.8.8"`) |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Query IVRE for all hosts with port 22 open and show their IP, banner, and country."
- "Use IVRE to find the top 10 most common web server products in the view database."
- "Count how many passive DNS records IVRE has for the domain example.com and its subdomains."
- "Query IVRE passive records for SSL certificates issued to *.example.com."
- "Get all hosts in the 10.0.0.0/8 range with open port 3306 from the IVRE scan database."
- "Use IVRE to look up geolocation and ASN data for IP address 203.0.113.42."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/ivre-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8366:8366 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8366 \
  hackerdogs/ivre-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "ivre-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/ivre-mcp:latest"],
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
    "ivre-mcp": {
      "url": "http://localhost:8366/mcp"
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
    "ivre-mcp": {
      "url": "http://localhost:8485/ivre-mcp/mcp",
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
| `MCP_PORT` | `8366` | HTTP port (only used with `streamable-http`) |
| `IVRE_WEB_URL` | `""` | Ivre web url |
| `IVRE_VERIFY_SSL` | `true` | Ivre verify ssl |

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
docker build -t hackerdogs/ivre-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name ivre-mcp-test -p 8366:8366 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/ivre-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8366/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8366/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8366/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"count_passive","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop ivre-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Ivre CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint ivre hackerdogs/ivre-mcp:latest --help
```
