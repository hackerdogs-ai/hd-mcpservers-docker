#!/usr/bin/env python3
"""ExifTool MCP Server — extract metadata from images, PDFs, and documents."""
import asyncio
import json
import logging
import os
import shutil
import sys
import tempfile
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("exiftool-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8502"))
mcp = FastMCP("ExifTool MCP Server", instructions="Extract metadata from images, PDFs, and documents using ExifTool.")
BIN = os.environ.get("EXIFTOOL_BIN", "exiftool")


def _find_binary() -> str:
    path = shutil.which(BIN)
    if not path:
        raise FileNotFoundError(f"exiftool not found. Install: apt-get install -y libimage-exiftool-perl")
    return path


def _is_url(v: str) -> bool:
    try:
        p = urlparse(v)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def _download(url: str, timeout: int = 30, max_bytes: int = 50 * 1024 * 1024) -> str:
    ext = os.path.splitext(urlparse(url).path)[1] or ""
    tmp = tempfile.NamedTemporaryFile(prefix="exif_", suffix=ext, delete=False)
    tmp_path = tmp.name
    tmp.close()
    written = 0
    req = Request(url, headers={"User-Agent": "exiftool-mcp/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp, open(tmp_path, "wb") as out:
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    raise ValueError(f"Download exceeds {max_bytes} bytes")
                out.write(chunk)
        return tmp_path
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


@mcp.tool()
async def exiftool_extract(
    file_path: str,
    extract_gps: bool = True,
    extract_author: bool = True,
    output_format: str = "json",
) -> str:
    """Extract metadata from an image, PDF, or document file.

    Args:
        file_path: Local file path or http(s) URL.
        extract_gps: Include GPS tags (default True).
        extract_author: Include author/creator tags (default True).
        output_format: 'json' (default) or 'text'.
    """
    binary = _find_binary()
    local_path = file_path
    temp_path = None
    try:
        if _is_url(file_path):
            temp_path = _download(file_path)
            local_path = temp_path

        if not os.path.isfile(local_path):
            return json.dumps({"error": f"File not found: {local_path}"})

        args = [binary]
        if output_format == "json":
            args += ["-j", "-G"]
        else:
            args += ["-S"]
        args += ["-a", "-u"]

        if not extract_gps:
            args += ["-x", "GPS*", "-x", "Composite:GPS*"]
        if not extract_author:
            args += ["-x", "Author", "-x", "Creator", "-x", "Producer", "-x", "Artist", "-x", "Copyright"]

        args.append(local_path)

        proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        out = stdout.decode("utf-8", errors="replace").strip()
        err = stderr.decode("utf-8", errors="replace").strip()

        if proc.returncode != 0:
            return json.dumps({"error": f"exiftool failed (exit {proc.returncode})", "detail": err or out})

        if output_format == "json" and out:
            return out
        return out or err or json.dumps({"message": "No metadata found"})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    logger.info("Starting exiftool-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
