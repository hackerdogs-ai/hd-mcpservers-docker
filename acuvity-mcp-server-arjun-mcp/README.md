<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Arjun MCP Server

MCP server for **Arjun** — HTTP parameter discovery (hidden GET/POST parameters). Wraps the Acuvity/Arjun image for MCP-compatible applications and AI workflows.

**Upstream:** [acuvity/mcp-server-arjun](https://hub.docker.com/r/acuvity/mcp-server-arjun) · [GitHub (cyproxio/mcp-for-security)](https://github.com/cyproxio/mcp-for-security/tree/HEAD/arjun-mcp)

## Docker Run (stdio)

```bash
docker run -i --rm acuvity/mcp-server-arjun:latest
```

## Env / Port

- Default: stdio transport. If the image supports HTTP streamable, use port **8382** and set `MCP_TRANSPORT=streamable-http`, `MCP_PORT=8382`.

## Tools

Exposes Arjun hidden parameter discovery for web security testing.
