<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Amass MCP Server

MCP server for **Amass** — subdomain reconnaissance (intel, enum, viz, track). Wraps the Acuvity/Amass image for MCP-compatible applications and AI workflows.

**Upstream:** [acuvity/mcp-server-amass](https://hub.docker.com/r/acuvity/mcp-server-amass) · [GitHub (cyproxio/mcp-for-security)](https://github.com/cyproxio/mcp-for-security/tree/HEAD/amass-mcp)

## Docker Run (stdio)

```bash
docker run -i --rm acuvity/mcp-server-amass:latest
```

## Env / Port

- Default: stdio transport. If the image supports HTTP streamable, use port **8381** and set `MCP_TRANSPORT=streamable-http`, `MCP_PORT=8381`.

## Tools

Exposes Amass subdomain enumeration and reconnaissance capabilities.
