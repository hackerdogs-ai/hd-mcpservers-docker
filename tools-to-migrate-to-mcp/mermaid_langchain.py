"""
Mermaid Rendering Tool for LangChain Agents
==========================================

This module provides a LangChain tool for rendering Mermaid diagrams to SVG or PNG.

It supports 3 input modes (exactly one must be provided):
- Local file path (expects `.mmd`)
- URL to a `.mmd` file (http(s) or file://)
- Raw Mermaid diagram string content

It uses the `mermaid-cli` Python library (Playwright-based renderer):
  https://github.com/seigok/mermaid-cli-python/tree/main

Notes on themes / colors:
- Mermaid themes are controlled via mermaid_config: {"theme": "..."} (e.g., "default", "forest", "dark", "neutral").
- Background color can be set via the renderer `background_color` parameter.
- Default background color uses Hackerdogs branding colors (see `shared.hackerdogs_colors.HackerdogsColors`).
  (The repo also has a Streamlit branding module, but shared colors are centralized in HackerdogsColors.)

Return format:
- Always returns a JSON string with:
  - status: success|error
  - output_format: svg|png
  - mime_type: image/svg+xml|image/png
  - image_base64: base64 encoded bytes
  - svg_text: included only for svg (utf-8 text), convenient for downstream rendering
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from langchain.tools import tool, ToolRuntime

from hd_logging import setup_logger
from shared.hackerdogs_colors import HackerdogsColors
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug

logger = setup_logger(__name__, log_file_path="logs/mermaid_langchain_tool.log")


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
    """
    Read text content from an http(s) URL or file:// URL with size limits.
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("url must be a non-empty string")
    if not (_is_http_url(url) or _is_file_url(url)):
        raise ValueError("url must be http(s) or file://")

    req = Request(url, headers={"User-Agent": "hackerdogs-mermaid-render/1.0"})
    try:
        with urlopen(req, timeout=timeout_s) as resp:
            data = resp.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise ValueError(f"URL content too large (> {max_bytes} bytes)")
            # Mermaid is text; assume UTF-8 (fallback replace)
            return data.decode("utf-8", errors="replace")
    except (HTTPError, URLError) as e:
        raise ValueError(f"Failed to read URL: {str(e)}") from e


def _resolve_mermaid_source(
    *,
    input_file: Optional[str],
    input_url: Optional[str],
    content: Optional[str],
) -> Tuple[str, str]:
    """
    Returns (source_kind, mermaid_definition_text)
    """
    provided = [bool(input_file), bool(input_url), bool(content)]
    if sum(provided) != 1:
        raise ValueError("Provide exactly one of input_file, input_url, or content")

    if input_file:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"input_file not found: {input_file}")
        if not input_file.lower().endswith(".mmd"):
            raise ValueError("input_file must end with .mmd")
        return "file", open(input_file, "r", encoding="utf-8", errors="replace").read()

    if input_url:
        return "url", _read_text_from_url(input_url)

    # content
    if not isinstance(content, str) or not content.strip():
        raise ValueError("content must be a non-empty string")
    return "content", content


def _run_coro_in_new_thread(coro) -> Any:
    """
    Run an async coroutine in a dedicated thread.

    This avoids 'asyncio.run() cannot be called from a running event loop' when tools
    are invoked from async contexts.
    """
    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(lambda: asyncio.run(coro))
        return fut.result()


def _render_mermaid_bytes(
    *,
    definition: str,
    output_format: str,
    theme: str,
    background_color: str,
    width: int,
    height: int,
    scale: int,
    css: Optional[str],
) -> bytes:
    """
    Render Mermaid diagram definition to bytes using mermaid-cli Python library.
    """
    try:
        from mermaid_cli import render_mermaid  # lazy import for clearer ImportError
    except ImportError as e:
        raise ImportError(
            "mermaid-cli is not installed. Install it with: pip install mermaid-cli "
            "and ensure Playwright browsers are installed: playwright install chromium"
        ) from e

    async def _do_render() -> bytes:
        _, _, data = await render_mermaid(
            definition=definition,
            output_format=output_format,
            background_color=background_color,
            viewport={"width": int(width), "height": int(height), "deviceScaleFactor": int(scale)},
            mermaid_config={"theme": theme},
            css=css,
        )
        return data

    return _run_coro_in_new_thread(_do_render())


@tool
def mermaid_render_diagram(
    runtime: ToolRuntime,
    input_file: Optional[str] = None,
    input_url: Optional[str] = None,
    content: Optional[str] = None,
    output_format: str = "svg",
    theme: str = "dark",
    background_color: Optional[str] = None,
    width: int = 1024,
    height: int = 768,
    scale: int = 2,
    css: Optional[str] = None,
    timeout_s: int = 60,
) -> str:
    """
    Render Mermaid (.mmd) diagrams to SVG or PNG.

    Inputs (exactly one):
    - input_file: Local path to a .mmd file
    - input_url: URL to a .mmd file (http(s) or file://)
    - content: Raw Mermaid definition string

    Args:
        runtime: ToolRuntime (injected by agent). Only used for optional context.
        output_format: "svg" or "png"
        theme: Mermaid theme ("default", "forest", "dark", "neutral")
        background_color: Background color. If None, defaults to Hackerdogs dark navy.
        width/height/scale: Viewport and scaling controls.
        css: Optional CSS string to apply to output.
        timeout_s: Best-effort timeout for URL reads (does not hard-stop Playwright).

    Returns:
        JSON string with base64-encoded image and metadata.
    """
    try:
        safe_log_info(
            logger,
            "[mermaid_render_diagram] Starting",
            input_file=input_file,
            input_url=input_url,
            has_content=bool(content),
            output_format=output_format,
            theme=theme,
            width=width,
            height=height,
            scale=scale,
        )

        if output_format not in ("svg", "png"):
            return json.dumps({"status": "error", "message": "output_format must be 'svg' or 'png'"})

        if background_color is None or not str(background_color).strip():
            background_color = HackerdogsColors.DARK_NAVY_BACKGROUND

        # Resolve input -> definition text
        kind, definition = _resolve_mermaid_source(input_file=input_file, input_url=input_url, content=content)
        safe_log_debug(logger, "[mermaid_render_diagram] Source resolved", source_kind=kind, definition_len=len(definition))

        # Render
        # NOTE: timeout_s currently only affects URL reads; Playwright rendering time is content-dependent.
        # Keep this arg for future use.
        _ = timeout_s
        data = _render_mermaid_bytes(
            definition=definition,
            output_format=output_format,
            theme=theme,
            background_color=str(background_color),
            width=width,
            height=height,
            scale=scale,
            css=css,
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
            "background_color": background_color,
            "note": "For SVG, you may use svg_text directly or decode image_base64.",
        }
        if output_format == "svg":
            try:
                result["svg_text"] = data.decode("utf-8", errors="replace")
            except Exception:
                pass

        safe_log_info(logger, "[mermaid_render_diagram] Complete", output_format=output_format, bytes_len=len(data))
        return json.dumps(result, indent=2)
    except Exception as e:
        safe_log_error(logger, "[mermaid_render_diagram] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"Mermaid render failed: {str(e)}"})


