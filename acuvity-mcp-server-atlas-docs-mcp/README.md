<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Atlas Docs MCP Server

MCP server for **Atlas Docs** — technical documentation for libraries and frameworks, processed into clean markdown for LLM consumption. Easy to use with Cursor, Cline, and other MCP clients.

**Upstream:** [acuvity/mcp-server-atlas-docs](https://hub.docker.com/r/acuvity/mcp-server-atlas-docs) · [GitHub (CartographAI/atlas-docs-mcp)](https://github.com/CartographAI/atlas-docs-mcp)

## Docker Run (stdio)

```bash
docker run -i --rm acuvity/mcp-server-atlas-docs:latest
```

## Env / Port

- Default: stdio transport. If the image supports HTTP streamable, use port **8384** and set `MCP_TRANSPORT=streamable-http`, `MCP_PORT=8384`.

## Tools

Exposes documentation lookup and processing for libraries and frameworks.
