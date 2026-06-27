<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# AWS Network MCP Server

MCP server wrapper for [AWS Network](https://github.com/awslabs/mcp/tree/main/src/aws-network-mcp-server) — read-only inspection and troubleshooting of AWS networking resources including Cloud WAN, Transit Gateway, VPC, Network Firewall, and VPN.

## What is AWS Network MCP?

The AWS Network MCP server provides read-only access to the full range of AWS networking services — VPCs, subnets, route tables, security groups, Transit Gateway attachments, Cloud WAN global networks, Network Firewall policies, and Site-to-Site VPN connections. Built from the `awslabs.aws-network-mcp-server` package (version 0.0.9+), it is purpose-built for troubleshooting connectivity issues and auditing network topology through natural language. See [awslabs/mcp](https://github.com/awslabs/mcp) for full documentation.

**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.

## Tools Reference

| Tool | Description |
|------|-------------|
| `get_path_trace_methodology` | Get Path Trace Methodology |
| `find_ip_address` | Find Ip Address |
| `get_eni_details` | Get Eni Details |
| `detect_cwan_inspection` | Detect Cwan Inspection |
| `get_all_cwan_routes` | Get All Cwan Routes |
| `get_cwan_routes` | Get Cwan Routes |
| `get_cwan_attachment` | Get Cwan Attachment |
| `get_cwan` | Get Cwan |
| `get_cwan_logs` | Get Cwan Logs |
| `get_cwan_peering` | Get Cwan Peering |
| `list_cwan_peerings` | List Cwan Peerings |
| `list_core_networks` | List Core Networks |
| `simulate_cwan_route_change` | Simulate Cwan Route Change |
| `get_firewall_rules` | Get Firewall Rules |
| `get_firewall_flow_logs` | Get Firewall Flow Logs |
| `list_firewalls` | List Firewalls |
| `detect_tgw_inspection` | Detect Tgw Inspection |
| `get_all_tgw_routes` | Get All Tgw Routes |
| `get_tgw` | Get Tgw |
| `get_tgw_routes` | Get Tgw Routes |
| `get_tgw_flow_logs` | Get Tgw Flow Logs |
| `list_tgw_peerings` | List Tgw Peerings |
| `list_transit_gateways` | List Transit Gateways |
| `get_vpc_flow_logs` | Get Vpc Flow Logs |
| `get_vpc_network` | Get Vpc Network |
| `list_vpcs` | List Vpcs |
| `list_vpn_connections` | List Vpn Connections |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List all VPCs in us-east-1 and show their CIDR blocks and flow log status."
- "Show me the Transit Gateway route tables and their associations in my account."
- "Which security groups allow inbound traffic on port 22 from 0.0.0.0/0?"
- "Describe the Cloud WAN global network and list its core network segments."
- "Check the status of all Site-to-Site VPN connections and flag any that are down."
- "Show the Network Firewall policies applied to each VPC in my account."

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
  hackerdogs/aws-network-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8618:8618 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8618 \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-network-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "aws-network-mcp": {
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
        "hackerdogs/aws-network-mcp:latest"
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
    "aws-network-mcp": {
      "url": "http://localhost:8618/mcp"
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
| `MCP_PORT` | `8618` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/aws-network-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name aws-network-mcp-test -p 8618:8618 \
  -e MCP_TRANSPORT=streamable-http \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-network-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8618/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8618/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8618/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop aws-network-mcp-test
```
