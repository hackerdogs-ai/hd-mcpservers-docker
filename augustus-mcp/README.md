<p align="center">
  <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="200"/>
</p>

# Augustus MCP Server

MCP server wrapper for [Augustus](https://github.com/praetorian-inc/augustus) — LLM adversarial vulnerability testing with 210+ probes and support for 28 LLM providers.

## What is Augustus?

Augustus is an LLM security testing tool by Praetorian that tests language models against adversarial attacks including prompt injection, jailbreaks, encoding exploits, and data extraction. It includes 210+ probes and supports 28 LLM providers out of the box.

## Prerequisites

Augustus scans LLMs for vulnerabilities, so it needs **API keys for the LLM providers you want to test**. At least one provider key is required.

| Provider | Environment Variable | Get Key |
|----------|---------------------|---------|
| OpenAI | `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| Anthropic | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| Cohere | `COHERE_API_KEY` | [dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys) |
| Google | `GOOGLE_API_KEY` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| Mistral | `MISTRAL_API_KEY` | [console.mistral.ai](https://console.mistral.ai) |
| Together AI | `TOGETHER_API_KEY` | [api.together.xyz](https://api.together.xyz) |
| Azure OpenAI | `AZURE_OPENAI_API_KEY` | Azure Portal |
| Groq | `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) |
| Ollama (local) | None needed | — |
| Test (dev) | None needed | — |

See the full [Augustus docs](https://github.com/praetorian-inc/augustus) for all 28 supported providers.

## Tools Reference

### `scan_llm`

Run an adversarial vulnerability scan against an LLM using 210+ probes.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `generator` | string | Yes | — | LLM provider (e.g. `"openai.OpenAI"`, `"anthropic.Anthropic"`, `"ollama.OllamaChat"`) |
| `model` | string | No | — | Model name (e.g. `"gpt-4"`, `"claude-3-opus"`, `"llama3.2:3b"`) |
| `probes` | string | No | — | Comma-separated probe names (e.g. `"dan.Dan_11_0"`) |
| `probes_glob` | string | No | — | Glob pattern for probes (e.g. `"dan.*,goodside.*"`) |
| `all_probes` | boolean | No | `false` | Run all 210+ probes |
| `detector` | string | No | — | Specific detector name |
| `detectors_glob` | string | No | — | Glob pattern for detectors |
| `buff` | string | No | — | Buff transformation (e.g. `"encoding.Base64"`) |
| `buffs_glob` | string | No | — | Glob pattern for buffs |
| `config_json` | string | No | — | JSON config for generator (e.g. `'{"temperature":0.7}'`) |
| `output_format` | string | No | `"json"` | Output: `"json"`, `"jsonl"`, or `"table"` |
| `concurrency` | integer | No | `10` | Max concurrent probes |
| `timeout` | string | No | `"30m"` | Scan timeout (e.g. `"30m"`, `"1h"`) |
| `verbose` | boolean | No | `false` | Enable verbose output |

<details>
<summary>Example response</summary>

```json
{
  "summary": {"total_probes": 5, "passed": 3, "failed": 2},
  "results": [{"probe": "dan.Dan_11_0", "status": "failed", "response": "..."}]
}
```

</details>

### `list_components`

List available Augustus components (probes, detectors, generators, harnesses, buffs). _No parameters._

### `get_version`

Get the installed Augustus version and build info. _No parameters._

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Run a DAN jailbreak test against GPT-4 and tell me if it's vulnerable."
- "Test my local Ollama model llama3.2:3b for prompt injection vulnerabilities."
- "Run all 210+ adversarial probes against the Anthropic Claude 3 Haiku model."
- "Test GPT-4 with base64 encoding buffs to see if encoded prompts can bypass safety filters."
- "List all available Augustus probes, detectors, and generators."
- "Run the goodside and dan probe categories against my OpenAI GPT-4o-mini deployment and report which ones fail."

## Deploy

### Docker Compose (recommended)

```bash
OPENAI_API_KEY=your_key docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e OPENAI_API_KEY=your_key \
  hackerdogs/augustus-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8101:8101 \
  -e OPENAI_API_KEY=your_key \
  -e ANTHROPIC_API_KEY=your_key \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8101 \
  hackerdogs/augustus-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "augustus-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "OPENAI_API_KEY",
        "-e", "ANTHROPIC_API_KEY",
        "hackerdogs/augustus-mcp:latest"
      ],
      "env": {
        "OPENAI_API_KEY": "<your-openai-api-key>",
        "ANTHROPIC_API_KEY": "<your-anthropic-api-key>"
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
    "augustus-mcp": {
      "url": "http://localhost:8101/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | API key for scanning OpenAI models |
| `ANTHROPIC_API_KEY` | — | API key for scanning Anthropic models |
| `COHERE_API_KEY` | — | API key for scanning Cohere models |
| `AZURE_OPENAI_API_KEY` | — | API key for scanning Azure OpenAI models |
| `GROQ_API_KEY` | — | API key for scanning Groq models |
| `MISTRAL_API_KEY` | — | API key for scanning Mistral models |
| `TOGETHER_API_KEY` | — | API key for scanning Together AI models |
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8101` | Port for streamable-http transport |

## Build

```bash
docker build -t hackerdogs/augustus-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name augustus-test -p 8101:8101 \
  -e MCP_TRANSPORT=streamable-http \
  -e OPENAI_API_KEY=your_key \
  hackerdogs/augustus-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8101/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8101/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool (list components):**

```bash
curl -s -X POST http://localhost:8101/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_components","arguments":{}}}'
```

**4. Call a tool (scan LLM):**

```bash
curl -s --max-time 120 -X POST http://localhost:8101/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"scan_llm","arguments":{"generator":"openai.OpenAI","model":"gpt-4o-mini","probes":"dan.Dan_11_0"}}}'
```

**5. Clean up:**

```bash
docker stop augustus-test
```
