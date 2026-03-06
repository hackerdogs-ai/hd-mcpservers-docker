# IVRE MCP Server

MCP server for [IVRE](https://ivre.rocks/) — a network reconnaissance framework. Connects to an existing IVRE deployment's Web API to expose scan results, passive reconnaissance data, passive DNS, network flows, and IP geolocation as MCP tools.

## Architecture

This server acts as an HTTP client to an already-running IVRE instance. It does **not** bundle a database or IVRE itself — it queries the IVRE Web API over HTTP.

```
MCP Client (Cursor/Claude) ──MCP──▶ ivre-mcp container ──HTTP──▶ IVRE Web (ivre/web) ──▶ MongoDB
```

### Prerequisites

You need a running IVRE deployment with the Web API accessible. The standard IVRE Docker stack (`ivre/db` + `ivre/web` + `ivre/client`) or any IVRE installation with `ivre httpd` running will work.

**New to IVRE?** See [DEPLOY_IVRE.md](DEPLOY_IVRE.md) for a complete step-by-step guide to deploying IVRE with Docker.

## Quick Start

### With Docker (stdio mode)

```bash
docker run -i --rm \
  -e IVRE_WEB_URL=http://your-ivre-host:80 \
  -e MCP_TRANSPORT=stdio \
  hackerdogs/ivre-mcp:latest
```

### With Docker (streamable-http mode)

```bash
docker run -d --rm \
  -e IVRE_WEB_URL=http://your-ivre-host:80 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8366 \
  -p 8366:8366 \
  hackerdogs/ivre-mcp:latest
```

The MCP endpoint will be available at `http://localhost:8366/mcp`.

### With Docker Compose

```bash
# Set your IVRE URL
export IVRE_WEB_URL=http://your-ivre-host:80

docker compose up
```

The compose file runs in streamable-http mode on port 8366 by default.

### Claude Desktop / Cursor Configuration

**stdio mode** (local, recommended for desktop use):

```json
{
  "mcpServers": {
    "ivre-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "IVRE_WEB_URL",
        "-e", "MCP_TRANSPORT",
        "hackerdogs/ivre-mcp:latest"
      ],
      "env": {
        "IVRE_WEB_URL": "http://your-ivre-instance:80",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

**streamable-http mode** (remote / Hackerdogs deployment):

```json
{
  "mcpServers": {
    "ivre-mcp": {
      "url": "http://localhost:8366/mcp"
    }
  }
}
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `IVRE_WEB_URL` | Yes | — | Base URL of the IVRE web interface (e.g., `http://ivre-web:80`) |
| `IVRE_VERIFY_SSL` | No | `true` | Set to `false` to skip SSL certificate verification |
| `MCP_TRANSPORT` | No | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | No | `8366` | Port for streamable-http transport |

## Tools

### Query Tools

| Tool | Description |
|------|-------------|
| `query_hosts` | Query hosts from the scan or view database with full details (ports, services, banners, OS, scripts) |
| `count_hosts` | Count hosts matching a filter |
| `query_passive` | Query passive reconnaissance records (DNS, HTTP headers, SSL certs, SSH keys) |
| `count_passive` | Count passive records matching a filter |

### Aggregation Tools

| Tool | Description |
|------|-------------|
| `top_values` | Get the most common values for a field (top services, ports, products, countries, etc.) |
| `distinct_values` | Get all distinct values for a field with counts |

### Specialized Query Tools

| Tool | Description |
|------|-------------|
| `get_host_ips` | Get only IP addresses matching a filter (compact output for target lists) |
| `get_ips_ports` | Get IPs with their open ports |
| `get_timeline` | Get scan timeline data for time-series analysis |

### Enrichment Tools

| Tool | Description |
|------|-------------|
| `ip_data` | Get geolocation and AS number data for an IP address |
| `passive_dns` | Query passive DNS records (Common Output Format compatible) |
| `query_flows` | Query aggregated network flow data |

## IVRE Filter Syntax

The `filter` parameter across tools uses IVRE's web filter syntax:

| Filter | Example | Description |
|--------|---------|-------------|
| `port:N` | `port:22` | Hosts with port N open |
| `service:S` | `service:http` | Hosts running service S |
| `hostname:H` | `hostname:example.com` | Hosts with hostname H |
| `country:CC` | `country:US` | Hosts in country CC |
| `net:CIDR` | `net:10.0.0.0/8` | Hosts in a network range |
| `product:P` | `product:Apache` | Hosts running product P |
| `version:V` | `version:2.4` | Hosts with version V |
| `cert.issuer:I` | `cert.issuer:Let's Encrypt` | Certificate issuer filter |
| `cpe.vendor:V` | `cpe.vendor:microsoft` | CPE vendor filter |
| `category:C` | `category:SCAN-001` | Scan category filter |
| `source:S` | `source:MyScanner` | Scan source filter |

Multiple filters separated by spaces are **ANDed**. Use the `OR` keyword for OR logic.

## Example Usage

**Find all hosts with SSH open in a specific network:**
```
query_hosts(filter="port:22 net:192.168.0.0/16", limit=20)
```

**Get top 10 services across all scanned hosts:**
```
top_values(field="service", limit=10)
```

**Look up passive DNS for a domain:**
```
passive_dns(query="example.com", include_subdomains=True)
```

**Get geolocation for an IP:**
```
ip_data(address="8.8.8.8")
```

**Count hosts running Apache:**
```
count_hosts(filter="product:Apache")
```

## Building

```bash
# Build locally
docker build -t hackerdogs/ivre-mcp:latest .

# Or use the publish script
./publish_to_hackerdogs.sh --build hackerdogs
```

## Network Configuration

When running alongside an IVRE Docker stack, ensure both containers share a Docker network:

```bash
# If IVRE runs on network 'ivre_network':
docker run -i --rm \
  --network ivre_network \
  -e IVRE_WEB_URL=http://ivre-web:80 \
  -e MCP_TRANSPORT=stdio \
  hackerdogs/ivre-mcp:latest
```

## References

- [IVRE Documentation](https://doc.ivre.rocks/)
- [IVRE Web API](https://doc.ivre.rocks/en/latest/dev/web-api.html)
- [IVRE GitHub](https://github.com/ivre/ivre)
- [IVRE Docker Images](https://hub.docker.com/u/ivre/)


## Running the tool directly (bypassing MCP)

This MCP server does not wrap a single CLI binary; it talks to an **IVRE web API** (see `IVRE_WEB_URL`). To run IVRE CLI tools (e.g. `ivre run`, `ivre ipinfo`) directly, use the [official IVRE Docker images](https://hub.docker.com/u/ivre/) instead of this image.
