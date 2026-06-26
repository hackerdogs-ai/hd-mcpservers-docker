<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Prowler MCP Server

MCP server wrapper for [Prowler](https://github.com/prowler-cloud/prowler) — cloud security posture management and compliance auditing for AWS, Azure, GCP, and Kubernetes.

## What is Prowler?

Prowler is an open-source cloud security tool that performs hundreds of security checks across AWS, Azure, GCP, and Kubernetes environments, mapping findings to compliance frameworks such as CIS, SOC 2, PCI-DSS, HIPAA, GDPR, and NIST. This image provides a local stub for local development and CI; for full cloud security scanning connect to the hosted Prowler MCP at `https://mcp.prowler.com/mcp`. See [prowler-cloud/prowler](https://github.com/prowler-cloud/prowler) for full documentation.

**No API keys required for the local stub** — the full production MCP at [mcp.prowler.com/mcp](https://mcp.prowler.com/mcp) may require authentication.

**Tools:**
- `remote_endpoint_info` — Return the official hosted Prowler MCP URL and connection notes.

## Tools Reference

### `remote_endpoint_info`

Return the official remote MCP URL and notes for the Prowler integration.

Returns the URL `https://mcp.prowler.com/mcp` and guidance on connecting your MCP client directly to the production Prowler cloud security service.

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "What is the hosted Prowler MCP endpoint I should connect to for cloud security scanning?"
- "Run a CIS AWS Foundations Benchmark check on my AWS account using Prowler."
- "List all Prowler security checks available for Azure and filter by HIGH severity."
- "Check my AWS environment for publicly exposed S3 buckets and unencrypted EBS volumes."
- "Generate a SOC 2 compliance report for my GCP project using Prowler checks."
- "Scan my Kubernetes cluster for misconfigurations against the CIS Kubernetes Benchmark."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/prowler-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8515:8515 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8515 \
  hackerdogs/prowler-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "prowler-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/prowler-mcp:latest"],
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
    "prowler-mcp": {
      "url": "http://localhost:8515/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8515` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/prowler-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name prowler-mcp-test -p 8515:8515 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/prowler-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8515/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8515/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8515/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"remote_endpoint_info","arguments":{}}}'
```

**4. Clean up:**

```bash
docker stop prowler-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Prowler MCP server in the same container by overriding the entrypoint without starting the MCP wrapper.

**Show help:**

```bash
docker run -i --rm --entrypoint python hackerdogs/prowler-mcp:latest mcp_server.py --help
```
