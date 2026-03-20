#!/usr/bin/env python3
"""Visualization Tools MCP Server — generate charts and graphs."""
import base64
import io
import json
import logging
import os
import sys
from typing import Optional

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("visualization-tools-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8506"))
mcp = FastMCP("Visualization Tools MCP Server", instructions="Generate charts and graphs from data using matplotlib.")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    MPL_AVAILABLE = True
except ImportError:
    MPL_AVAILABLE = False


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return b64


def _save_fig(fig, output_path: Optional[str]) -> dict:
    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return {"status": "success", "file": output_path}
    b64 = _fig_to_base64(fig)
    return {"status": "success", "image_base64": b64[:100] + "...(truncated)", "image_format": "png", "full_base64_length": len(b64)}


@mcp.tool()
def create_bar_chart(data_json: str, title: str = "Bar Chart", xlabel: str = "", ylabel: str = "", output_path: Optional[str] = None) -> str:
    """Create a bar chart from JSON data.

    Args:
        data_json: JSON object with "labels" (list) and "values" (list of numbers).
        title: Chart title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        output_path: File path to save PNG (optional, returns base64 if omitted).
    """
    if not MPL_AVAILABLE:
        return json.dumps({"error": "matplotlib not installed"})
    try:
        d = json.loads(data_json)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(d["labels"], d["values"])
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=45)
        return json.dumps(_save_fig(fig, output_path))
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def create_line_chart(data_json: str, title: str = "Line Chart", xlabel: str = "", ylabel: str = "", output_path: Optional[str] = None) -> str:
    """Create a line chart from JSON data.

    Args:
        data_json: JSON object with "x" (list) and "y" (list of numbers), or "series" (list of {name, x, y}).
        title: Chart title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        output_path: File path to save PNG.
    """
    if not MPL_AVAILABLE:
        return json.dumps({"error": "matplotlib not installed"})
    try:
        d = json.loads(data_json)
        fig, ax = plt.subplots(figsize=(10, 6))
        if "series" in d:
            for s in d["series"]:
                ax.plot(s["x"], s["y"], label=s.get("name", ""))
            ax.legend()
        else:
            ax.plot(d["x"], d["y"])
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        return json.dumps(_save_fig(fig, output_path))
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def create_pie_chart(data_json: str, title: str = "Pie Chart", output_path: Optional[str] = None) -> str:
    """Create a pie chart.

    Args:
        data_json: JSON object with "labels" (list) and "values" (list of numbers).
        title: Chart title.
        output_path: File path to save PNG.
    """
    if not MPL_AVAILABLE:
        return json.dumps({"error": "matplotlib not installed"})
    try:
        d = json.loads(data_json)
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(d["values"], labels=d["labels"], autopct="%1.1f%%")
        ax.set_title(title)
        return json.dumps(_save_fig(fig, output_path))
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def create_scatter_plot(data_json: str, title: str = "Scatter Plot", xlabel: str = "", ylabel: str = "", output_path: Optional[str] = None) -> str:
    """Create a scatter plot.

    Args:
        data_json: JSON object with "x" and "y" (lists of numbers).
        title: Chart title.
        output_path: File path to save PNG.
    """
    if not MPL_AVAILABLE:
        return json.dumps({"error": "matplotlib not installed"})
    try:
        d = json.loads(data_json)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(d["x"], d["y"], alpha=0.6)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        return json.dumps(_save_fig(fig, output_path))
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    logger.info("Starting visualization-tools-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
