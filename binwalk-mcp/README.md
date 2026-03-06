<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Binwalk MCP Server

MCP server wrapper for [Binwalk](https://github.com/ReFirmLabs/binwalk) — Firmware analysis and extraction.

## What is Binwalk?

Binwalk (binwalk) is a security tool that provides: **Firmware analysis and extraction.**

See [ReFirmLabs/binwalk](https://github.com/ReFirmLabs/binwalk) for full documentation.

**No API keys required** — Binwalk runs locally inside the Docker container.

**Summary.** MCP server wrapper for [Binwalk](https://github.com/ReFirmLabs/binwalk) — Firmware analysis and extraction.

**Tools:**
- `run_binwalk` — Run binwalk with the given arguments. Returns structured JSON output.
- `download_file` — Download a file or repository from a URL into the container workspace. Use this to pre-download content before running multiple analyses on the same data.
- `cleanup_downloads` — Remove downloaded files from the container workspace.


## Tools Reference

### `run_binwalk`

Run binwalk with the given arguments. Returns structured JSON output.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `source_url` | string | No | `""` | URL to download files into the container before running. Supports HTTP(S) files, archives (auto-extracted), and GitHub/GitLab repo URLs. Use `{source}` in arguments as a placeholder for the downloaded path. |
| `timeout_seconds` | integer | No | `600` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "binwalk output will appear here"
}
```

</details>

### `download_file`

Download a file or repository from a URL into the container workspace. Use this to pre-download content before running multiple analyses on the same data.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | — | HTTP(S) URL, GitHub/GitLab repo URL, or `data:` URI |
| `extract` | boolean | No | `true` | Auto-extract archives (`.zip`, `.tar.gz`, etc.) |

Returns JSON with `path` (local file path to use in other tools) and `job_id` (for cleanup).

### `cleanup_downloads`

Remove downloaded files from the container workspace.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `job_id` | string | No | `""` | Specific job ID to clean up. If empty, removes all downloads |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Run binwalk with --help to see all available options."
- "Use binwalk to scan the target 192.168.1.1."
- "What options does binwalk support? Show me its help output."
- "Run binwalk against example.com with default settings."
- "Execute binwalk with verbose output enabled."
- "Use the binwalk tool to analyze the target and report findings."

**URL-based ingestion (no volume mounts needed):**

- "Download the firmware from https://example.com/router-firmware.bin using source_url and analyze it with binwalk."
- "Use download_file to fetch https://example.com/firmware.bin, then run binwalk extraction on it."


## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/binwalk-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8241:8241 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8241 \
  hackerdogs/binwalk-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "binwalk-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/binwalk-mcp:latest"],
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
    "binwalk-mcp": {
      "url": "http://localhost:8241/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8241` | HTTP port (only used with `streamable-http`) |
| `HD_MAX_DOWNLOAD_MB` | `500` | Max file download size in MB (URL fetch) |
| `HD_FETCH_TIMEOUT` | `120` | Download timeout in seconds (URL fetch) |

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
docker build -t hackerdogs/binwalk-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name binwalk-mcp-test -p 8241:8241 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/binwalk-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8241/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8241/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8241/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_binwalk","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop binwalk-mcp-test
```


## Running the tool directly (bypassing MCP)

You can run the binwalk CLI in the same container by overriding the entrypoint to analyze and extract firmware/binaries without starting the MCP server.

**Scan a file (mount it):**

```bash
docker run -i --rm --entrypoint binwalk hackerdogs/binwalk-mcp:latest -B /path/to/file
```

**Show help:**

```bash
docker run -i --rm --entrypoint binwalk hackerdogs/binwalk-mcp:latest --help
```