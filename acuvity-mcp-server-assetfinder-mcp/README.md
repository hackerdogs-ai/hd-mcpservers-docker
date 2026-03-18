<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Assetfinder MCP Server

MCP server for **Assetfinder** — passive subdomain enumeration. Wraps the Acuvity/Assetfinder image for MCP-compatible applications and AI workflows.

**Upstream:** [acuvity/mcp-server-assetfinder](https://hub.docker.com/r/acuvity/mcp-server-assetfinder) · [GitHub (cyproxio/mcp-for-security)](https://github.com/cyproxio/mcp-for-security/tree/HEAD/assetfinder-mcp)

## Docker Run (stdio)

```bash
docker run -i --rm acuvity/mcp-server-assetfinder:latest
```

## Env / Port

- Default: stdio transport. If the image supports HTTP streamable, use port **8383** and set `MCP_TRANSPORT=streamable-http`, `MCP_PORT=8383`.

## Tools

Exposes Assetfinder passive subdomain discovery.
