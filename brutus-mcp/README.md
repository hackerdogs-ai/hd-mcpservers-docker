<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Brutus MCP Server

MCP server wrapper for [Brutus](https://github.com/praetorian-inc/brutus) — credential testing tool across 24 protocols by Praetorian.

## What is Brutus?

Brutus tests credentials against target hosts across **24 protocols** including SSH, RDP, MySQL, PostgreSQL, Redis, SMB, HTTP Basic Auth, FTP, Telnet, LDAP, SNMP, VNC, MongoDB, MSSQL, Oracle, Cassandra, Memcached, Elasticsearch, CouchDB, Neo4j, RabbitMQ, Kafka, MQTT, and more. It also includes RDP-specific checks for Network Level Authentication and sticky keys backdoor detection.

**No API keys required** — Brutus connects directly to target services using standard protocol handshakes.

## Tools Reference

### `test_credentials`

Test credentials against a target host across 24 supported protocols (SSH, RDP, MySQL, PostgreSQL, Redis, SMB, HTTP Basic Auth, FTP, Telnet, LDAP, SNMP, VNC, etc.).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `target` | string | Yes | — | Target in `host:port` format (e.g. `"192.168.1.1:22"`) |
| `protocol` | string | Yes | — | Protocol to test (e.g. `"ssh"`, `"rdp"`, `"mysql"`, `"redis"`) |
| `usernames` | string | No | `""` | Comma-separated usernames to test |
| `passwords` | string | No | `""` | Comma-separated passwords to test |
| `threads` | integer | No | `4` | Number of concurrent threads |
| `json_output` | boolean | No | `true` | Request JSON output |
| `verbose` | boolean | No | `false` | Enable verbose output |

<details>
<summary>Example response</summary>

```json
{
  "success": true,
  "output": [{"host": "192.168.1.1", "port": 22, "protocol": "ssh", "username": "admin", "valid": true}]
}
```

</details>

### `check_rdp_nla`

Check if an RDP target has Network Level Authentication (NLA) enabled.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `target` | string | Yes | — | Target in `host:port` format (e.g. `"192.168.1.1:3389"`) |
| `verbose` | boolean | No | `false` | Enable verbose output |

### `detect_sticky_keys`

Detect RDP sticky keys backdoor on a target.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `target` | string | Yes | — | Target in `host:port` format (e.g. `"192.168.1.1:3389"`) |
| `verbose` | boolean | No | `false` | Enable verbose output |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Test if the default SSH credentials admin/admin work on 192.168.1.50:22."
- "Check if the Redis instance at 10.0.0.12:6379 allows unauthenticated access."
- "Try the usernames root, admin, and ubuntu with passwords password, 123456, and admin on the MySQL server at 192.168.1.100:3306."
- "Check if the RDP server at 10.0.0.5:3389 has Network Level Authentication enabled."
- "Detect if there's a sticky keys backdoor on the Windows RDP host at 192.168.1.200:3389."
- "Test FTP anonymous login on 192.168.1.10:21."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/brutus-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8102:8102 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8102 \
  hackerdogs/brutus-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "brutus-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/brutus-mcp:latest"],
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
    "brutus-mcp": {
      "url": "http://localhost:8102/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8102` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/brutus-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name brutus-test -p 8102:8102 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/brutus-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8102/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8102/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8102/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"test_credentials","arguments":{"target":"192.168.1.1:22","protocol":"ssh","usernames":"admin","passwords":"admin"}}}'
```

**4. Clean up:**

```bash
docker stop brutus-test
```
