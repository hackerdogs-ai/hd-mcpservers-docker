<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Titus MCP Server

MCP server wrapper for [Titus](https://github.com/praetorian-inc/titus) — secret detection tool by Praetorian that scans source code, files, and git history for leaked credentials.

## What is Titus?

Titus scans source code, files, and git history for leaked API keys, tokens, credentials, and other secrets using **459 detection rules**. It supports scanning local directories as well as full git commit history to find secrets that may have been committed and later removed.

**No API keys required** — Titus runs entirely locally against your files and repositories.

**Summary.** MCP server wrapper for [Titus](https://github.com/praetorian-inc/titus) — secret detection tool by Praetorian that scans source code, files, and git history for leaked credentials.

**Tools:**
- `scan_path` — Scan files and directories for secrets (API keys, tokens, credentials) using 459 detection rules.
- `scan_git` — Scan git history for secrets leaked in past commits.
- `list_rules` — List all 459 available secret detection rules. _No parameters._
- `generate_report` — Generate a report from the most recent scan.
- `download_file` — Download a file or repository from a URL into the container workspace. Use this to pre-download content before running multiple analyses on the same data.
- `cleanup_downloads` — Remove downloaded files from the container workspace.


## Tools Reference

### `scan_path`

Scan files and directories for secrets (API keys, tokens, credentials) using 459 detection rules.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | string | Yes | — | Local path **or URL** to scan. Accepts a file/directory path, HTTP(S) URL, archive URL, or a GitHub/GitLab repo URL. URLs are downloaded into the container automatically |
| `validate` | boolean | No | `false` | Validate discovered secrets against live services |
| `output_format` | string | No | `"json"` | Output format: `"json"` or `"csv"` |
| `rules_include` | string | No | `""` | Rule IDs or tags to include (empty = all) |
| `rules_exclude` | string | No | `""` | Rule IDs or tags to exclude |

<details>
<summary>Example response</summary>

```json
{
  "success": true,
  "output": [
    {"rule_id": "aws-access-key", "file": "config.py", "line": 42, "match": "AKIA...XXXX", "severity": "high"}
  ]
}
```

</details>

### `scan_git`

Scan git history for secrets leaked in past commits.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | string | Yes | — | Local path **or URL** to a git repo. Accepts a directory path or a GitHub/GitLab repo URL (e.g. `https://github.com/org/repo`). URLs are cloned into the container automatically |
| `validate` | boolean | No | `false` | Validate discovered secrets |
| `output_format` | string | No | `"json"` | Output format: `"json"` or `"csv"` |
| `rules_include` | string | No | `""` | Rule IDs or tags to include |
| `rules_exclude` | string | No | `""` | Rule IDs or tags to exclude |

### `list_rules`

List all 459 available secret detection rules. _No parameters._

### `generate_report`

Generate a report from the most recent scan.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `output_format` | string | No | `"json"` | Output format: `"json"` or `"csv"` |

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

- "Scan the /app/project directory for any leaked API keys, tokens, or secrets."
- "Check the git history of /app/repo for any secrets that were committed and later removed."
- "Scan /app/code but only look for AWS-related secrets like access keys and secret keys."
- "List all the secret detection rules that Titus supports."
- "Scan /app/config and validate any discovered secrets against live services to check if they're still active."
- "Generate a report from the last scan in CSV format."

**URL-based ingestion (no volume mounts needed):**

- "Scan the repo at https://github.com/org/backend for leaked API keys, tokens, or secrets."
- "Check https://github.com/org/repo git history for any secrets that were committed and later removed."
- "Use download_file to fetch https://example.com/source.tar.gz, then scan the downloaded path for secrets."


## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/titus-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8103:8103 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8103 \
  hackerdogs/titus-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "titus-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/titus-mcp:latest"],
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
    "titus-mcp": {
      "url": "http://localhost:8103/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8103` | HTTP port (only used with `streamable-http`) |
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
docker build -t hackerdogs/titus-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name titus-test -p 8103:8103 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/titus-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8103/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8103/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8103/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_rules","arguments":{}}}'
```

**4. Clean up:**

```bash
docker stop titus-test
```


## Running the tool directly (bypassing MCP)

You can run the titus CLI in the same container by overriding the entrypoint for Titus container security without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint titus hackerdogs/titus-mcp:latest --help
```