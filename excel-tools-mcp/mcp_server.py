#!/usr/bin/env python3
"""Excel Tools MCP Server — read, write, and analyze spreadsheets."""
import json
import logging
import os
import sys
from typing import Optional

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("excel-tools-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8505"))
mcp = FastMCP("Excel Tools MCP Server", instructions="Read, write, and analyze Excel/CSV spreadsheets. Supports openpyxl and pandas.")

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


@mcp.tool()
def read_excel(file_path: str, sheet_name: Optional[str] = None, max_rows: int = 100) -> str:
    """Read an Excel file and return its contents as JSON.

    Args:
        file_path: Path to .xlsx or .xls file.
        sheet_name: Specific sheet name (default: first sheet).
        max_rows: Maximum rows to return (default 100).
    """
    if not PANDAS_AVAILABLE:
        return json.dumps({"error": "pandas not installed"})
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name or 0, nrows=max_rows)
        return json.dumps({
            "columns": list(df.columns),
            "rows": df.head(max_rows).to_dict(orient="records"),
            "shape": {"rows": df.shape[0], "columns": df.shape[1]},
        }, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def read_csv(file_path: str, delimiter: str = ",", max_rows: int = 100) -> str:
    """Read a CSV file and return its contents as JSON.

    Args:
        file_path: Path to CSV file.
        delimiter: Column delimiter (default comma).
        max_rows: Maximum rows to return.
    """
    if not PANDAS_AVAILABLE:
        return json.dumps({"error": "pandas not installed"})
    try:
        df = pd.read_csv(file_path, delimiter=delimiter, nrows=max_rows)
        return json.dumps({
            "columns": list(df.columns),
            "rows": df.head(max_rows).to_dict(orient="records"),
            "shape": {"rows": df.shape[0], "columns": df.shape[1]},
        }, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def describe_spreadsheet(file_path: str) -> str:
    """Get summary statistics for a spreadsheet (Excel or CSV).

    Args:
        file_path: Path to Excel or CSV file.
    """
    if not PANDAS_AVAILABLE:
        return json.dumps({"error": "pandas not installed"})
    try:
        if file_path.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        desc = df.describe(include="all").to_dict()
        return json.dumps({
            "columns": list(df.columns),
            "dtypes": {col: str(dt) for col, dt in df.dtypes.items()},
            "shape": {"rows": df.shape[0], "columns": df.shape[1]},
            "null_counts": df.isnull().sum().to_dict(),
            "statistics": desc,
        }, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_sheets(file_path: str) -> str:
    """List all sheet names in an Excel workbook.

    Args:
        file_path: Path to .xlsx file.
    """
    if not OPENPYXL_AVAILABLE:
        return json.dumps({"error": "openpyxl not installed"})
    try:
        wb = openpyxl.load_workbook(file_path, read_only=True)
        sheets = wb.sheetnames
        wb.close()
        return json.dumps({"sheets": sheets, "count": len(sheets)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def write_csv(file_path: str, data_json: str, columns: Optional[str] = None) -> str:
    """Write data to a CSV file.

    Args:
        file_path: Output path for the CSV.
        data_json: JSON array of objects (rows) to write.
        columns: Comma-separated column order (optional).
    """
    if not PANDAS_AVAILABLE:
        return json.dumps({"error": "pandas not installed"})
    try:
        rows = json.loads(data_json)
        df = pd.DataFrame(rows)
        if columns:
            cols = [c.strip() for c in columns.split(",")]
            df = df[cols]
        df.to_csv(file_path, index=False)
        return json.dumps({"status": "success", "file": file_path, "rows_written": len(df)})
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    logger.info("Starting excel-tools-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
