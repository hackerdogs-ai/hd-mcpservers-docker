# Alpaca MCP Server (Docker)

- **Docker Image**: `mcp/alpaca:latest` — **not on Docker Hub; you must build it locally.**
- **Description**: Alpaca Trading API via MCP (stocks, ETF, options, crypto, portfolio, market data).
- **Source**: [alpacahq/alpaca-mcp-server](https://github.com/alpacahq/alpaca-mcp-server)

## Build the image

There is no pre-built public image. From the repo:

```bash
git clone https://github.com/alpacahq/alpaca-mcp-server.git
cd alpaca-mcp-server
docker build -t mcp/alpaca:latest .
```

## Environment variables

- `ALPACA_API_KEY` (required) — from [Alpaca dashboard](https://app.alpaca.markets/)
- `ALPACA_SECRET_KEY` (required)
- `ALPACA_PAPER_TRADE` (optional) — `True` for paper trading

## Config (stdio)

Use in Cursor, Streamlit MCP registry, or Claude config:

```json
{
  "mcpServers": {
    "alpaca-mcp-server": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e", "ALPACA_API_KEY=your_key",
        "-e", "ALPACA_SECRET_KEY=your_secret",
        "-e", "ALPACA_PAPER_TRADE=True",
        "mcp/alpaca:latest"
      ]
    }
  }
}
```

The Streamlit MCP registry adds `--init` to `docker run` automatically for stable stdio. Replace `your_key` / `your_secret` with real keys (or use the tool’s environment variables in the app).
