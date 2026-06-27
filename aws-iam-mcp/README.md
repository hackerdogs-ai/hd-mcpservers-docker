<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# AWS IAM MCP Server

MCP server wrapper for [AWS IAM](https://github.com/awslabs/mcp/tree/main/src/iam-mcp-server) — inspect and manage AWS Identity and Access Management users, roles, policies, and permission boundaries.

## What is AWS IAM?

AWS Identity and Access Management (IAM) is the access control plane for all AWS services, letting you create and manage users, groups, roles, and fine-grained permission policies. This MCP server wraps the `awslabs.iam-mcp-server` package so you can query IAM state, audit trust relationships, and inspect policy documents through natural language. See [awslabs/mcp](https://github.com/awslabs/mcp) for full documentation.

**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.

## Tools Reference

| Tool | Description |
|------|-------------|
| `list_users` | List Users |
| `get_user` | Get User |
| `create_user` | Create User |
| `delete_user` | Delete User |
| `list_roles` | List Roles |
| `create_role` | Create Role |
| `list_policies` | List Policies |
| `get_managed_policy_document` | Get Managed Policy Document |
| `attach_user_policy` | Attach User Policy |
| `detach_user_policy` | Detach User Policy |
| `create_access_key` | Create Access Key |
| `delete_access_key` | Delete Access Key |
| `simulate_principal_policy` | Simulate Principal Policy |
| `list_groups` | List Groups |
| `get_group` | Get Group |
| `create_group` | Create Group |
| `delete_group` | Delete Group |
| `add_user_to_group` | Add User To Group |
| `remove_user_from_group` | Remove User From Group |
| `attach_group_policy` | Attach Group Policy |
| `detach_group_policy` | Detach Group Policy |
| `put_user_policy` | Put User Policy |
| `get_user_policy` | Get User Policy |
| `delete_user_policy` | Delete User Policy |
| `put_role_policy` | Put Role Policy |
| `get_role_policy` | Get Role Policy |
| `delete_role_policy` | Delete Role Policy |
| `list_user_policies` | List User Policies |
| `list_role_policies` | List Role Policies |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List all IAM roles in my account that have administrator access."
- "Show me the trust policy for the role named 'ECSTaskExecutionRole'."
- "Which IAM users have no MFA enabled in my account?"
- "Find all managed policies attached to the group 'Developers'."
- "List IAM roles that can be assumed by Lambda and show their permission boundaries."
- "Summarize the inline policies on user 'deploy-bot' and flag any overly broad permissions."

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
  hackerdogs/aws-iam-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8615:8615 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8615 \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-iam-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "aws-iam-mcp": {
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
        "hackerdogs/aws-iam-mcp:latest"
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
    "aws-iam-mcp": {
      "url": "http://localhost:8615/mcp"
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
| `MCP_PORT` | `8615` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/aws-iam-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name aws-iam-mcp-test -p 8615:8615 \
  -e MCP_TRANSPORT=streamable-http \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-iam-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8615/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8615/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8615/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop aws-iam-mcp-test
```
