"""
Graphviz DOT Rendering Tool for LangChain Agents
================================================

This module provides a LangChain tool for rendering Graphviz DOT (`.dot` / `.gv`) diagrams
to SVG or PNG.

It supports 3 input modes (exactly one must be provided):
- Local file path (expects `.dot` or `.gv`)
- URL to a `.dot`/`.gv` file (http(s) or file://)
- Raw DOT string content

Rendering is done via the Python `graphviz` package, which requires the Graphviz
system binaries (`dot`) installed and available on PATH.

Themes / colors:
- Graphviz supports graph/node/edge attributes. This tool provides:
  - a simple `theme` preset ("dark" or "light")
  - optional overrides via JSON strings: graph_attr_json / node_attr_json / edge_attr_json
- Default colors use Hackerdogs branding colors (see `shared.hackerdogs_colors.HackerdogsColors`).

Return format:
- Always returns a JSON string with:
  - status: success|error
  - output_format: svg|png
  - mime_type
  - image_base64 (base64 bytes)
  - svg_text included for svg
"""

from __future__ import annotations

import base64
import json
import os
import shutil
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from langchain.tools import tool, ToolRuntime

from hd_logging import setup_logger
from shared.hackerdogs_colors import HackerdogsColors
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug

logger = setup_logger(__name__, log_file_path="logs/graphviz_dot_langchain_tool.log")


def _is_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _is_file_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return parsed.scheme == "file" and bool(parsed.path)
    except Exception:
        return False


def _read_text_from_url(url: str, timeout_s: int = 30, max_bytes: int = 5 * 1024 * 1024) -> str:
    if not isinstance(url, str) or not url.strip():
        raise ValueError("url must be a non-empty string")
    if not (_is_http_url(url) or _is_file_url(url)):
        raise ValueError("url must be http(s) or file://")

    req = Request(url, headers={"User-Agent": "hackerdogs-graphviz-render/1.0"})
    try:
        with urlopen(req, timeout=timeout_s) as resp:
            data = resp.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise ValueError(f"URL content too large (> {max_bytes} bytes)")
            return data.decode("utf-8", errors="replace")
    except (HTTPError, URLError) as e:
        raise ValueError(f"Failed to read URL: {str(e)}") from e


def _resolve_dot_source(
    *,
    input_file: Optional[str],
    input_url: Optional[str],
    content: Optional[str],
) -> Tuple[str, str]:
    provided = [bool(input_file), bool(input_url), bool(content)]
    if sum(provided) != 1:
        raise ValueError("Provide exactly one of input_file, input_url, or content")

    if input_file:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"input_file not found: {input_file}")
        if not (input_file.lower().endswith(".dot") or input_file.lower().endswith(".gv")):
            raise ValueError("input_file must end with .dot or .gv")
        return "file", open(input_file, "r", encoding="utf-8", errors="replace").read()

    if input_url:
        return "url", _read_text_from_url(input_url)

    if not isinstance(content, str) or not content.strip():
        raise ValueError("content must be a non-empty string")
    return "content", content


def _parse_json_dict(s: Optional[str]) -> Dict[str, str]:
    if not s:
        return {}
    try:
        parsed = json.loads(s)
        if not isinstance(parsed, dict):
            raise ValueError("must be a JSON object")
        # Graphviz expects string values for attrs
        out: Dict[str, str] = {}
        for k, v in parsed.items():
            out[str(k)] = str(v)
        return out
    except Exception as e:
        raise ValueError(f"Invalid JSON dict: {str(e)}") from e


def _theme_defaults(theme: str) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    """
    Returns (graph_attr, node_attr, edge_attr)
    """
    t = (theme or "").strip().lower()
    if t not in ("dark", "light"):
        raise ValueError("theme must be 'dark' or 'light'")

    if t == "dark":
        graph_attr = {
            "bgcolor": HackerdogsColors.DARK_NAVY_BACKGROUND,
            "fontcolor": HackerdogsColors.PRIMARY_TEXT_ON_DARK_BACKGROUND_OFF_WHITE,
            "fontname": "Helvetica",
        }
        node_attr = {
            "style": "rounded,filled",
            "color": HackerdogsColors.AQUA_BLUE_PRIMARY,
            "fillcolor": HackerdogsColors.SECONDARY_TEXT_ON_LIGHT_BACKGROUND_SLATE_GRAY,
            "fontcolor": HackerdogsColors.PRIMARY_TEXT_ON_DARK_BACKGROUND_OFF_WHITE,
            "fontname": "Helvetica",
        }
        edge_attr = {
            "color": HackerdogsColors.AQUA_BLUE_PRIMARY,
            "fontcolor": HackerdogsColors.PRIMARY_TEXT_ON_DARK_BACKGROUND_OFF_WHITE,
            "fontname": "Helvetica",
        }
        return graph_attr, node_attr, edge_attr

    # light
    graph_attr = {
        "bgcolor": "transparent",
        "fontcolor": HackerdogsColors.PRIMARY_TEXT_ON_LIGHT_BACKGROUND_DARK_NAVY,
        "fontname": "Helvetica",
    }
    node_attr = {
        "style": "rounded,filled",
        "color": HackerdogsColors.SECONDARY_TEXT_ON_LIGHT_BACKGROUND_SLATE_GRAY,
        "fillcolor": HackerdogsColors.SOFT_GREEN_BG_CARDS_SUCCESS,
        "fontcolor": HackerdogsColors.PRIMARY_TEXT_ON_LIGHT_BACKGROUND_DARK_NAVY,
        "fontname": "Helvetica",
    }
    edge_attr = {
        "color": HackerdogsColors.SECONDARY_TEXT_ON_LIGHT_BACKGROUND_SLATE_GRAY,
        "fontcolor": HackerdogsColors.SECONDARY_TEXT_ON_LIGHT_BACKGROUND_SLATE_GRAY,
        "fontname": "Helvetica",
    }
    return graph_attr, node_attr, edge_attr


def _render_dot_bytes(
    *,
    dot_text: str,
    output_format: str,
    graph_attr: Dict[str, str],
    node_attr: Dict[str, str],
    edge_attr: Dict[str, str],
) -> bytes:
    try:
        from graphviz import Source  # lazy import for clearer ImportError
    except ImportError as e:
        raise ImportError("Python package 'graphviz' is not installed. Install with: pip install graphviz") from e

    if not shutil.which("dot"):
        raise RuntimeError("Graphviz 'dot' binary not found on PATH. Install graphviz system package.")

    def _escape(v: str) -> str:
        # Escape quotes and backslashes for DOT strings
        return str(v).replace("\\", "\\\\").replace('"', '\\"')

    def _attrs_stmt(kind: str, attrs: Dict[str, str]) -> Optional[str]:
        if not attrs:
            return None
        parts = [f'{k}="{_escape(v)}"' for k, v in attrs.items()]
        return f"{kind} [{', '.join(parts)}];"

    def _inject_attrs(text: str) -> str:
        """
        Inject graph/node/edge default attributes into an existing DOT graph.

        The Python `graphviz.Source` class doesn't expose `.graph_attr` / `.node_attr` / `.edge_attr`
        like `graphviz.Digraph` does, so we inject DOT statements right after the opening `{`.
        """
        graph_line = _attrs_stmt("graph", graph_attr)
        node_line = _attrs_stmt("node", node_attr)
        edge_line = _attrs_stmt("edge", edge_attr)
        injected_lines = [l for l in [graph_line, node_line, edge_line] if l]
        if not injected_lines:
            return text

        brace_idx = text.find("{")
        if brace_idx == -1:
            return "\n".join(injected_lines) + "\n" + text

        prefix = text[: brace_idx + 1]
        suffix = text[brace_idx + 1 :]
        injection = "\n  " + "\n  ".join(injected_lines) + "\n"
        return prefix + injection + suffix

    src = Source(_inject_attrs(dot_text))

    return src.pipe(format=output_format)


@tool
def graphviz_render_dot(
    runtime: ToolRuntime,
    input_file: Optional[str] = None,
    input_url: Optional[str] = None,
    content: Optional[str] = None,
    output_format: str = "svg",
    theme: str = "dark",
    graph_attr_json: Optional[str] = None,
    node_attr_json: Optional[str] = None,
    edge_attr_json: Optional[str] = None,
    timeout_s: int = 30,
) -> str:
    """
    Render Graphviz DOT (.dot/.gv) diagrams to SVG or PNG.

    Inputs (exactly one):
    - input_file: Local path to a .dot/.gv file
    - input_url: URL to a .dot/.gv file (http(s) or file://)
    - content: Raw DOT definition string

    Args:
        runtime: ToolRuntime (injected by agent). Only used for optional context.
        output_format: "svg" or "png"
        theme: "dark" or "light"
        graph_attr_json/node_attr_json/edge_attr_json: Optional JSON objects (strings) of Graphviz attributes.
            Example: '{"rankdir":"LR","bgcolor":"transparent"}'
        timeout_s: URL read timeout in seconds.

    Returns:
        JSON string with base64-encoded image and metadata.
    """
    try:
        safe_log_info(
            logger,
            "[graphviz_render_dot] Starting",
            input_file=input_file,
            input_url=input_url,
            has_content=bool(content),
            output_format=output_format,
            theme=theme,
        )

        if output_format not in ("svg", "png"):
            return json.dumps({"status": "error", "message": "output_format must be 'svg' or 'png'"})

        kind, dot_text = _resolve_dot_source(input_file=input_file, input_url=input_url, content=content)
        safe_log_debug(logger, "[graphviz_render_dot] Source resolved", source_kind=kind, dot_len=len(dot_text))

        # Defaults + overrides
        graph_attr, node_attr, edge_attr = _theme_defaults(theme)
        graph_attr.update(_parse_json_dict(graph_attr_json))
        node_attr.update(_parse_json_dict(node_attr_json))
        edge_attr.update(_parse_json_dict(edge_attr_json))

        _ = timeout_s  # currently only affects URL reads inside resolver
        data = _render_dot_bytes(
            dot_text=dot_text,
            output_format=output_format,
            graph_attr=graph_attr,
            node_attr=node_attr,
            edge_attr=edge_attr,
        )

        if not data:
            return json.dumps({"status": "error", "message": "Renderer returned empty output"})

        b64 = base64.b64encode(data).decode("utf-8")
        mime = "image/svg+xml" if output_format == "svg" else "image/png"

        result: Dict[str, Any] = {
            "status": "success",
            "output_format": output_format,
            "mime_type": mime,
            "image_base64": b64,
            "bytes_len": len(data),
            "theme": theme,
            "note": "For SVG, you may use svg_text directly or decode image_base64.",
        }
        if output_format == "svg":
            try:
                result["svg_text"] = data.decode("utf-8", errors="replace")
            except Exception:
                pass

        safe_log_info(logger, "[graphviz_render_dot] Complete", output_format=output_format, bytes_len=len(data))
        return json.dumps(result, indent=2)
    except Exception as e:
        safe_log_error(logger, "[graphviz_render_dot] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"Graphviz render failed: {str(e)}"})


