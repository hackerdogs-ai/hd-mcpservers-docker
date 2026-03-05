<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# TLSx MCP Server

MCP server wrapper for [TLSx](https://github.com/projectdiscovery/tlsx) — fast TLS grabber by ProjectDiscovery.

## What is TLSx?

TLSx is a fast TLS grabber for **certificate data collection, TLS configuration analysis, and misconfiguration detection**. It extracts SANs, CN, organization, TLS version, cipher suites, JARM, and JA3 fingerprints across hosts, IPs, CIDRs, URLs, and ASNs. It detects expired, self-signed, and hostname-mismatched certificates.

**No API keys required** — TLSx connects directly to targets using standard TLS handshakes.

## Tools Reference

### `scan_tls`

Scan TLS configuration and certificate data for one or more targets.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `hosts` | string | Yes | — | Comma-separated targets (IP, hostname, CIDR, URL, ASN) |
| `ports` | string | No | `"443"` | Comma-separated ports to scan |
| `show_san` | boolean | No | `true` | Show Subject Alternative Names |
| `show_cn` | boolean | No | `true` | Show Common Name |
| `show_org` | boolean | No | `false` | Show Subject Organization |
| `tls_version` | boolean | No | `false` | Show TLS version |
| `cipher` | boolean | No | `false` | Show cipher suite |
| `jarm` | boolean | No | `false` | Compute JARM fingerprint |
| `ja3` | boolean | No | `false` | Compute JA3 hash |
| `enumerate_versions` | boolean | No | `false` | Enumerate all supported TLS versions |
| `enumerate_ciphers` | boolean | No | `false` | Enumerate all supported cipher suites |

<details>
<summary>Example response</summary>

```json
{
  "success": true,
  "output": [
    {"host": "github.com", "ip": "140.82.116.4", "port": "443", "tls_version": "tls13", "cipher": "TLS_AES_128_GCM_SHA256"}
  ]
}
```

</details>

### `check_misconfigurations`

Check for TLS certificate misconfigurations (expired, self-signed, hostname mismatch).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `hosts` | string | Yes | — | Comma-separated targets |
| `check_expired` | boolean | No | `true` | Check for expired certificates |
| `check_self_signed` | boolean | No | `true` | Check for self-signed certificates |
| `check_mismatched` | boolean | No | `true` | Check for hostname mismatches |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Check the TLS certificate on github.com and show me the SANs and CN."
- "What TLS version and cipher suite does hackerdogs.ai use?"
- "Scan 10.0.0.1:443 and 10.0.0.2:443 for expired or self-signed certificates."
- "Get the JARM fingerprint for cloudflare.com to identify its TLS stack."
- "Enumerate all supported TLS versions and cipher suites on example.com."
- "Check if the certificate on my staging server at staging.example.com:8443 has a hostname mismatch."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/tlsx-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8109:8109 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8109 \
  hackerdogs/tlsx-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "tlsx-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/tlsx-mcp:latest"],
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
    "tlsx-mcp": {
      "url": "http://localhost:8109/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8109` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/tlsx-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name tlsx-test -p 8109:8109 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/tlsx-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8109/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8109/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8109/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"scan_tls","arguments":{"hosts":"github.com"}}}'
```

**4. Clean up:**

```bash
docker stop tlsx-test
```
