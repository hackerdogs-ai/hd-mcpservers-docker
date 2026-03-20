#!/usr/bin/env python3
"""VictoriaLogs MCP Server — log analysis with LogsQL."""
import json, logging, os, sys
import httpx
from fastmcp import FastMCP
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("victorialogs-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8527"))
mcp = FastMCP("VictoriaLogs MCP Server", instructions="Log analysis with LogsQL queries via VictoriaLogs.")
VL_URL = os.environ.get("VICTORIALOGS_URL", "http://localhost:9428")

def _vl_get(path, params):
    try:
        r = httpx.get(f"{VL_URL}{path}", params=params, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def victorialogs_query(query: str, limit: int = 100) -> str:
    """Query VictoriaLogs using LogsQL.
    Args: query: LogsQL query string. limit: Max log lines."""
    return _vl_get("/select/logsql/query", {"query": query, "limit": limit})

@mcp.tool()
def victorialogs_hits(query: str, step: str = "1h") -> str:
    """Get hit counts over time for a LogsQL query.
    Args: query: LogsQL query. step: Time bucket (e.g. 1h, 15m)."""
    return _vl_get("/select/logsql/hits", {"query": query, "step": step})

@mcp.tool()
def victorialogs_stats(query: str) -> str:
    """Get statistics for a LogsQL query.
    Args: query: LogsQL query."""
    return _vl_get("/select/logsql/stats_query", {"query": query})

@mcp.tool()
def victorialogs_field_names(query: str) -> str:
    """Get field names from logs matching a query.
    Args: query: LogsQL query."""
    return _vl_get("/select/logsql/field_names", {"query": query})

if __name__ == "__main__":
    logger.info("Starting victorialogs-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
