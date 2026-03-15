<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Suricata MCP Server

MCP server wrapper for [Suricata](https://suricata.io/) — network intrusion detection and prevention system (IDS/IPS).

## What is Suricata?

Suricata (suricata) is a security tool that provides: **high-performance network intrusion detection (IDS), intrusion prevention (IPS), and network security monitoring. It inspects network traffic using rules and signatures to detect threats, malware, and policy violations.**

See [suricata.io](https://suricata.io/) and the [OISF/suricata](https://github.com/OISF/suricata) repository for full documentation.

**No API keys required** — Suricata runs locally inside the Docker container with default rules from Emerging Threats.

**Summary.** MCP server wrapper for [Suricata](https://suricata.io/) — network intrusion detection and prevention system.

**Tools:**
- `run_suricata` — Run suricata with the given arguments. Returns command output.
- `analyze_pcap` — Analyze a PCAP file and return alerts and EVE JSON events.
- `download_file` — Download files/repos from URLs into the container for analysis.
- `cleanup_downloads` — Clean up downloaded files from the container workspace.


## Tools Reference

### `run_suricata`

Run suricata with the given arguments. Returns command output.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `"-V"` or `"-r /path/to/file.pcap -l /app/output"`) |
| `source_url` | string | No | `""` | HTTP(S) URL to download; use `{source}` placeholder in arguments |
| `timeout_seconds` | integer | No | `600` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```
This is Suricata version 6.0.10 RELEASE
```

</details>

### `analyze_pcap`

Analyze a PCAP file with Suricata and return alerts from fast.log and EVE JSON events.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `pcap_path` | string | No | `""` | Path to a PCAP file already in the container |
| `source_url` | string | No | `""` | HTTP(S) URL to download the PCAP from |
| `timeout_seconds` | integer | No | `600` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "return_code": 0,
  "alerts": "03/15/2026-12:00:00.000000  [**] [1:2001219:20] ET SCAN ...",
  "eve_events_count": 42,
  "alert_events": [...]
}
```

</details>

### `download_file`

Download a file or repository from a URL into the container workspace.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | — | HTTP(S) URL, GitHub/GitLab repo URL, or data: URI |
| `extract` | boolean | No | `true` | Automatically extract archives (.zip, .tar.gz, etc.) |

### `cleanup_downloads`

Clean up downloaded files from the container workspace.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `job_id` | string | No | `""` | Specific job ID to clean up. If empty, removes all downloads. |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use Suricata to analyze this PCAP file and show me any detected threats."
- "Download this PCAP from the URL and run Suricata IDS analysis on it."
- "Show me the Suricata version and build info with -V and --build-info."
- "Run Suricata against the network capture and summarize the alerts."
- "List all Suricata rule categories currently loaded."
- "Analyze the traffic capture at this URL for any malware signatures."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/suricata-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8365:8365 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8365 \
  hackerdogs/suricata-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "suricata-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/suricata-mcp:latest"],
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
    "suricata-mcp": {
      "url": "http://localhost:8365/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8365` | HTTP port (only used with `streamable-http`) |
| `SURICATA_BIN` | `suricata` | Path or name of the Suricata binary |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "nuclei", "naabu", "julius").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use Suricata to analyze this PCAP capture"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/suricata-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name suricata-mcp-test -p 8365:8365 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/suricata-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8365/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8365/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8365/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_suricata","arguments":{"arguments":"-V"}}}'
```

**4. Clean up:**

```bash
docker stop suricata-mcp-test
```


## Running the tool directly (bypassing MCP)

You can run Suricata directly in the same container by overriding the entrypoint to analyze traffic without starting the MCP server.

**Show version:**

```bash
docker run --rm --entrypoint suricata hackerdogs/suricata-mcp:latest -V
```

**Show build info:**

```bash
docker run --rm --entrypoint suricata hackerdogs/suricata-mcp:latest --build-info
```

**Analyze a PCAP file:**

```bash
docker run --rm -v /path/to/captures:/data --entrypoint suricata hackerdogs/suricata-mcp:latest -r /data/capture.pcap -l /data/output
```
