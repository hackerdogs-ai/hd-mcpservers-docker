<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# ggshield MCP Server

MCP server wrapper for [ggshield](https://github.com/GitGuardian/ggshield) — Secret detection and code security scanning by GitGuardian.

## What is ggshield?

ggshield (ggshield) is a security tool that provides: **Secret detection and code security scanning by GitGuardian.**

See [GitGuardian/ggshield](https://github.com/GitGuardian/ggshield) for full documentation.

**No API keys required** — ggshield runs locally inside the Docker container.

**Summary.** MCP server wrapper for [ggshield](https://github.com/GitGuardian/ggshield) — Secret detection and code security scanning by GitGuardian.

**Tools:**
- `run_ggshield` — Run ggshield with the given arguments. Returns structured JSON output.
- `download_file` — Download a file or repository from a URL into the container workspace. Use this to pre-download content before running multiple analyses on the same data.
- `cleanup_downloads` — Remove downloaded files from the container workspace.


## Tools Reference

### `run_ggshield`

Run ggshield with the given arguments. Returns structured JSON output.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `source_url` | string | No | `""` | URL to download files into the container before running. Supports HTTP(S) files, archives (auto-extracted), and GitHub/GitLab repo URLs. Use `{source}` in arguments as a placeholder for the downloaded path. |
| `timeout_seconds` | integer | No | `600` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "ggshield output will appear here"
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

- "Run ggshield with --help to see all available options."
- "Use ggshield to scan the target 192.168.1.1."
- "What options does ggshield support? Show me its help output."
- "Run ggshield against example.com with default settings."
- "Execute ggshield with verbose output enabled."
- "Use the ggshield tool to analyze the target and report findings."

**URL-based ingestion (no volume mounts needed):**

- "Scan https://github.com/org/repo for leaked credentials using ggshield with source_url."
- "Download and scan https://example.com/source.zip for secrets with ggshield."


## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/ggshield-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8363:8363 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8363 \
  hackerdogs/ggshield-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "ggshield-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/ggshield-mcp:latest"],
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
    "ggshield-mcp": {
      "url": "http://localhost:8363/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8363` | HTTP port (only used with `streamable-http`) |
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
docker build -t hackerdogs/ggshield-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name ggshield-mcp-test -p 8363:8363 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/ggshield-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8363/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8363/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8363/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_ggshield","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop ggshield-mcp-test
```


## Running the tool directly (bypassing MCP)

You can run the ggshield CLI in the same container by overriding the entrypoint to scan for secrets (e.g. GitGuardian) without starting the MCP server.

**Scan repo (mount it):**

```bash
docker run -i --rm --entrypoint ggshield hackerdogs/ggshield-mcp:latest secret scan path /path/to/repo
```

**Show help:**

```bash
docker run -i --rm --entrypoint ggshield hackerdogs/ggshield-mcp:latest --help
```