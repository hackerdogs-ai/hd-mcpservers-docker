#!/usr/bin/env python3
"""TestDisk MCP Server — Stateless disk partition recovery and file carving.

Downloads a disk image from a provided URL, analyzes it using TestDisk/PhotoRec,
and securely cleans up the environment afterwards.
"""

import asyncio
import json
import logging
import os
import shutil
import sys
import uuid

from fastmcp import FastMCP
import hd_fetch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("testdisk-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8283"))

mcp = FastMCP(
    "TestDisk MCP Server",
    instructions=(
        "Stateless disk analysis. Provide a URL to a disk image. The server will download it, "
        "analyze it with testdisk or photorec, and return the results."
    ),
)

TESTDISK_BIN = os.environ.get("TESTDISK_BIN", "/usr/bin/testdisk")
PHOTOREC_BIN = os.environ.get("PHOTOREC_BIN", "/usr/bin/photorec")
WORKSPACE_DIR = "/app/temp_workspace"


async def _download_file(url: str, dest_path: str, timeout_seconds: int = 300) -> bool:
    """Download a file via wget."""
    logger.info(f"Downloading image from {url}...")
    try:
        proc = await asyncio.create_subprocess_exec(
            "wget", "-q", "-O", dest_path, url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
        if proc.returncode == 0 and os.path.exists(dest_path):
            return True
        logger.error(f"Wget failed with exit code {proc.returncode}")
        return False
    except asyncio.TimeoutError:
        logger.error(f"Download timed out after {timeout_seconds}s")
        if proc:
            proc.kill()
        return False
    except Exception as e:
        logger.error(f"Download exception: {e}")
        return False


async def _run_command(cmd: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a command and return structured output."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=WORKSPACE_DIR
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout_seconds}s.",
            "return_code": -1,
        }
    except Exception as exc:
        return {
            "stdout": "",
            "stderr": f"Failed to execute command: {exc}",
            "return_code": -1,
        }

    return {
        "stdout": stdout_bytes.decode("utf-8", errors="replace"),
        "stderr": stderr_bytes.decode("utf-8", errors="replace"),
        "return_code": proc.returncode,
    }


@mcp.tool()
async def analyze_remote_disk(
    image_url: str,
    tool: str = "testdisk",
    arguments: str = "/list",
    timeout_seconds: int = 600,
) -> str:
    """Download a disk image from a URL and analyze it.

    Args:
        image_url: Direct HTTP/HTTPS link to the disk image (.dd, .img, etc.).
        tool: Which binary to use ("testdisk" or "photorec").
        arguments: Additional non-interactive arguments (e.g., "/list").
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    import shlex

    tool = tool.lower().strip()
    if tool not in ["testdisk", "photorec"]:
        return json.dumps({"error": True, "message": "Tool must be 'testdisk' or 'photorec'."})

    binary = TESTDISK_BIN if tool == "testdisk" else PHOTOREC_BIN
    if not shutil.which(binary):
        return json.dumps({"error": True, "message": f"{binary} binary not found in container."})

    # Generate a unique temporary filename
    temp_filename = f"image_{uuid.uuid4().hex}.dd"
    temp_filepath = os.path.join(WORKSPACE_DIR, temp_filename)

    # 1. Download the image
    success = await _download_file(image_url, temp_filepath, timeout_seconds=300)
    if not success:
        return json.dumps({"error": True, "message": f"Failed to download image from {image_url}."})

    # 2. Prepare command
    args = shlex.split(arguments) if arguments.strip() else []
    cmd = [binary] + args + [temp_filepath]
    
    logger.info(f"Running command: {' '.join(cmd)}")

    # 3. Execute
    result = await _run_command(cmd, timeout_seconds=timeout_seconds)

    # 4. Clean up the downloaded image immediately to save space
    if os.path.exists(temp_filepath):
        os.remove(temp_filepath)
        logger.info(f"Cleaned up temporary file: {temp_filepath}")

    if result["return_code"] != 0:
        return json.dumps({
            "error": True,
            "message": f"{tool} failed (exit code {result['return_code']})",
            "detail": result["stderr"] or result["stdout"] or "Unknown error",
            "command": " ".join(cmd),
        }, indent=2)

    return json.dumps({
        "success": True,
        "tool": tool,
        "stdout": result["stdout"].strip()
    }, indent=2)


def main():
    logger.info("Starting testdisk-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()