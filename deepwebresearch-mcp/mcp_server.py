#!/usr/bin/env python3
"""Deep Web Research MCP Server — fetch and extract content from URLs for research.

Fetches URLs and returns cleaned text (and optional metadata) for use in research workflows.
"""

import json
import logging
import os
import re
import sys
from html import unescape
import httpx
from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("deepwebresearch-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8377"))

mcp = FastMCP(
    "Deep Web Research MCP Server",
    instructions="Fetch URLs and extract text for research. Use fetch_url for one URL or fetch_urls for multiple. Optional max_chars to truncate (default 50000).",
)

MAX_CHARS_DEFAULT = 50_000
MAX_CHARS_MAX = 500_000
REQUEST_TIMEOUT = 30.0


def _strip_html(html: str) -> str:
    """Remove tags and decode entities; collapse whitespace."""
    text = re.sub(r"<script[^>]*>[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<style[^>]*>[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


@mcp.tool()
def fetch_url(url: str, max_chars: int = 50000) -> str:
    """Fetch a single URL and return extracted text and metadata (status, content_type). Optional max_chars to limit length (default 50000)."""
    if not url or not url.strip():
        return json.dumps({"error": "url is required"})
    url = url.strip()
    max_chars = max(1000, min(max_chars, MAX_CHARS_MAX))
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
            r = client.get(url)
            r.raise_for_status()
            text = _strip_html(r.text)
            if len(text) > max_chars:
                text = text[:max_chars] + "\n...[truncated]"
            return json.dumps(
                {
                    "url": url,
                    "status_code": r.status_code,
                    "content_type": r.headers.get("content-type", "").split(";")[0].strip(),
                    "text_length": len(text),
                    "text": text,
                },
                indent=2,
            )
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "url": url, "body_preview": (e.response.text or "")[:300]})
    except Exception as e:
        logger.exception("fetch_url failed")
        return json.dumps({"error": str(e), "url": url})


@mcp.tool()
def fetch_urls(urls: str, max_chars_per_url: int = 20000) -> str:
    """Fetch multiple URLs (comma- or newline-separated) and return extracted text for each. Optional max_chars_per_url (default 20000)."""
    if not urls or not urls.strip():
        return json.dumps({"error": "urls is required"})
    raw = re.split(r"[\n,]+", urls.strip())
    url_list = [u.strip() for u in raw if u.strip()]
    if not url_list:
        return json.dumps({"error": "no valid URLs"})
    max_per = max(1000, min(max_chars_per_url, MAX_CHARS_MAX))
    results = []
    with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        for url in url_list[:20]:
            try:
                r = client.get(url)
                r.raise_for_status()
                text = _strip_html(r.text)
                if len(text) > max_per:
                    text = text[:max_per] + "\n...[truncated]"
                results.append({"url": url, "status_code": r.status_code, "text_length": len(text), "text": text})
            except Exception as e:
                results.append({"url": url, "error": str(e)})
    return json.dumps({"results": results}, indent=2)


if __name__ == "__main__":
    logger.info("Starting deepwebresearch-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
