# SecOps MCP Server

Run security CLI tools (nuclei, subfinder, naabu, ffuf, nmap, etc.) via a whitelisted subprocess bridge. Extend the image (or use a base with tools on PATH) to add subfinder, nuclei, etc.; use `list_tools` to see what is available.

- **Port:** 8379 (streamable-http)
- **Env:** `MCP_TRANSPORT`, `MCP_PORT`

## Tools

| Tool | Description |
|------|-------------|
| `list_tools` | List which allowed tools are installed on PATH. |
| `run_secops_tool` | Run a tool by name with CLI args. Args: `tool_name`, `args` (space-separated), optional `timeout_seconds` (default 120). |

Allowed tools: nuclei, subfinder, naabu, httpx, dnsx, katana, gau, waybackurls, ffuf, gobuster, nmap, amass, sqlmap, wfuzz, whatweb, nikto.

## Docker Run (stdio)

```bash
docker run -i --rm -e MCP_TRANSPORT=stdio hackerdogs/secops-mcp:latest
```

## Docker Run (HTTP streamable)

```bash
docker run -d -p 8379:8379 -e MCP_TRANSPORT=streamable-http -e MCP_PORT=8379 hackerdogs/secops-mcp:latest
```

Example: run subfinder for a domain: `run_secops_tool(tool_name="subfinder", args="-d example.com")`.
