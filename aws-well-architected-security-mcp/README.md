<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# AWS Well-Architected Security MCP Server

MCP server wrapper for [AWS Well-Architected Security](https://github.com/awslabs/mcp/tree/main/src/well-architected-security-mcp-server) — assess your AWS workloads against the Security pillar of the AWS Well-Architected Framework and surface high-risk findings.

## What is AWS Well-Architected Security?

The AWS Well-Architected Framework Security pillar provides guidance across six areas: IAM, detection, infrastructure protection, data protection, incident response, and application security. This MCP server (`awslabs.well-architected-security-mcp-server`) integrates with AWS Well-Architected Tool workloads to list reviews, retrieve question-by-question answers, and identify high-risk issues (HRIs) and medium-risk issues (MRIs) — enabling AI-assisted security gap analysis against AWS best practices. See [awslabs/mcp](https://github.com/awslabs/mcp) for full documentation.

**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.

## Tools Reference

| Tool | Description |
|------|-------------|
| `CheckSecurityServices` | Checksecurityservices |
| `GetSecurityFindings` | Getsecurityfindings |
| `GetStoredSecurityContext` | Getstoredsecuritycontext |
| `CheckStorageEncryption` | Checkstorageencryption |
| `ListServicesInRegion` | Listservicesinregion |
| `CheckNetworkSecurity` | Checknetworksecurity |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List all Well-Architected workloads in my account and their risk counts."
- "Show me the high-risk issues found in the Security pillar for the 'production-api' workload."
- "What security best practices does AWS recommend for the IAM area of the Well-Architected Framework?"
- "Summarize the medium-risk issues across all workloads in the Security pillar."
- "Which Well-Architected security questions have unanswered items in my 'payments' workload?"
- "Generate a remediation plan for the top 3 high-risk security findings in my Well-Architected review."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-well-architected-security-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8626:8626 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8626 \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-well-architected-security-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "aws-well-architected-security-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "-e",
        "AWS_REGION",
        "-e",
        "AWS_ACCESS_KEY_ID",
        "-e",
        "AWS_SECRET_ACCESS_KEY",
        "hackerdogs/aws-well-architected-security-mcp:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "AWS_REGION": "",
        "AWS_ACCESS_KEY_ID": "",
        "AWS_SECRET_ACCESS_KEY": ""
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
    "aws-well-architected-security-mcp": {
      "url": "http://localhost:8626/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `AWS_REGION` | — | AWS region (e.g. `us-east-1`) |
| `AWS_ACCESS_KEY_ID` | — | AWS access key ID |
| `AWS_SECRET_ACCESS_KEY` | — | AWS secret access key |
| `MCP_PORT` | `8626` | HTTP port (only used with `streamable-http`) |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name.
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly. If you don't specify, Hackerdogs will automatically choose the best tool for the job.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/aws-well-architected-security-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name aws-well-architected-security-mcp-test -p 8626:8626 \
  -e MCP_TRANSPORT=streamable-http \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-well-architected-security-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8626/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8626/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8626/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop aws-well-architected-security-mcp-test
```
