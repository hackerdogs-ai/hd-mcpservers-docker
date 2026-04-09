#!/usr/bin/env python3
"""File Operations MCP Server — file format conversion and analysis."""
import json, logging, os, sys
from fastmcp import FastMCP
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("file-operations-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8522"))
mcp = FastMCP("File Operations MCP Server", instructions="File format conversion between CSV, JSON, Excel.")

@mcp.tool()
def convert_csv_to_json(file_path: str) -> str:
    """Convert CSV file to JSON.
    Args: file_path: Path to CSV file."""
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        return json.dumps({"rows": df.to_dict(orient="records"), "count": len(df)}, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def convert_json_to_csv(file_path: str, output_path: str) -> str:
    """Convert JSON file to CSV.
    Args: file_path: Path to JSON file. output_path: Output CSV path."""
    try:
        import pandas as pd
        with open(file_path) as f: data = json.load(f)
        df = pd.DataFrame(data if isinstance(data, list) else [data])
        df.to_csv(output_path, index=False)
        return json.dumps({"status": "success", "output": output_path, "rows": len(df)})
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def file_info(file_path: str) -> str:
    """Get file information (size, type, modification time).
    Args: file_path: Path to file."""
    try:
        stat = os.stat(file_path)
        return json.dumps({"path": file_path, "size_bytes": stat.st_size, "modified": stat.st_mtime, "exists": True})
    except FileNotFoundError:
        return json.dumps({"path": file_path, "exists": False})
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting file-operations-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
