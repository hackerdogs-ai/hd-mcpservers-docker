<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Julius MCP Server

MCP server wrapper for [Julius](https://github.com/praetorian-inc/julius) — LLM service fingerprinting tool by Praetorian.

## What is Julius?

Julius fingerprints **33+ LLM services** running on network endpoints. It sends crafted HTTP probes and matches response signatures to identify the exact server infrastructure — Ollama, vLLM, LiteLLM, HuggingFace TGI, LocalAI, LM Studio, NVIDIA NIM, llama.cpp, Aphrodite, FastChat, GPT4All, KoboldCpp, gateway proxies, RAG platforms, and more.

**No API keys required** — Julius runs entirely offline and only sends standard HTTP requests.

**Summary.** MCP server wrapper for [Julius](https://github.com/praetorian-inc/julius) — LLM service fingerprinting tool by Praetorian.

**Tools:**
- `probe_targets` — Probe one or more target URLs to fingerprint which LLM service is running. Detects 33+ services including Ollama, vLLM, LiteLLM, HuggingFace TGI, LocalAI, LM Studio, NVIDIA NIM, and more.
- `list_probes` — List all available probe definitions that Julius can use for fingerprinting LLM services.
- `validate_probes` — Validate custom probe definition files (YAML/JSON).
- `download_file` — Download a file or repository from a URL into the container workspace. Use this to pre-download content before running multiple analyses on the same data.
- `cleanup_downloads` — Remove downloaded files from the container workspace.


## Tools Reference

### `probe_targets`

Probe one or more target URLs to fingerprint which LLM service is running. Detects 33+ services including Ollama, vLLM, LiteLLM, HuggingFace TGI, LocalAI, LM Studio, NVIDIA NIM, and more.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `targets` | string | Yes | — | Space-separated target URLs (e.g. `"http://host:11434 https://host2:8000"`) |
| `output_format` | string | No | `"json"` | Output format — `"json"` or `"jsonl"` |
| `concurrency` | integer | No | `10` | Number of concurrent probes |
| `timeout` | integer | No | `5` | Per-probe HTTP timeout in seconds |
| `quiet` | boolean | No | `false` | Suppress informational output, only return matches |
| `verbose` | boolean | No | `false` | Enable verbose output for debugging |

<details>
<summary>Example response</summary>

```json
{
  "success": true,
  "output": [
    {
      "target": "http://192.168.4.174:11434/",
      "service": "ollama",
      "matched_request": "/",
      "category": "self-hosted",
      "specificity": 100,
      "models": ["qwen3-coder:latest", "qwen3:latest"]
    }
  ]
}
```

</details>

### `list_probes`

List all available probe definitions that Julius can use for fingerprinting LLM services.

_No parameters._

### `validate_probes`

Validate custom probe definition files (YAML/JSON).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | string | Yes | — | Local path **or URL** to the probe definition file to validate. HTTP(S) URLs are downloaded into the container automatically |

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

- "Scan http://192.168.1.100:8080 and tell me what LLM service is running on it."
- "Check all these endpoints for LLM services: http://10.0.0.5:11434 http://10.0.0.6:8000 http://10.0.0.7:3000"
- "Is there an Ollama instance running on my local network at 192.168.4.174?"
- "Probe https://api.example.com and identify if it's using vLLM, TGI, or another inference server."
- "List all the probe types that Julius supports for fingerprinting LLM services."
- "Scan my staging AI endpoints with high concurrency and a 10-second timeout per probe."

**URL-based ingestion (no volume mounts needed):**

- "Download custom probe definitions from https://example.com/custom-probes.yaml using download_file and validate them."
- "Fetch the probe file from https://example.com/probes.json and validate it with julius."


## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/julius-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8100:8100 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8100 \
  hackerdogs/julius-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "julius-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/julius-mcp:latest"],
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
    "julius-mcp": {
      "url": "http://localhost:8100/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8100` | HTTP port (only used with `streamable-http`) |
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
docker build -t hackerdogs/julius-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name julius-test -p 8100:8100 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/julius-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8100/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8100/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8100/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"probe_targets","arguments":{"targets":"http://example.com:80"}}}'
```

**4. Clean up:**

```bash
docker stop julius-test
```
