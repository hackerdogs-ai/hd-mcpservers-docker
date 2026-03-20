# Httpx MCP Server

Hackerdogs MCP wrapper for Httpx — probe and analyze HTTP servers. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_httpx`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/httpx-mcpatest`
- **HTTP:** `docker run -d -p 8386:8386 -e MCP_TRANSPORT=streamable-http hackerdogs/httpx-mcpatest` → `http://localhost:8386/mcp/`

## mcpServer.json

```json
{
  "mcpServers": {
    "httpx-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "MCP_PORT", "hackerdogs/httpx-mcpatest"],
      "env": { "MCP_TRANSPORT": "stdio", "MCP_PORT": "8386" }
    }
  }
}
```

## Contributing

1. **Fork the repository** (if you don't have write access).
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/hd-mcpservers-docker.git
   cd hd-mcpservers-docker
   ```
3. **Add upstream remote** (optional, for syncing):
   ```bash
   git remote add upstream https://github.com/hackerdogs/hd-mcpservers-docker.git
   ```
4. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
5. **Make your changes**, then commit:
   ```bash
   git add .
   git commit -m "Add: brief description of your feature"
   ```
6. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Open a Pull Request** on GitHub from your branch into `main` (or the default branch), with a clear title and description of your feature.
