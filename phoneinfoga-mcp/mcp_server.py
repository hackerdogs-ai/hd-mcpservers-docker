#!/usr/bin/env python3
"""PhoneInfoga MCP Server — phone number OSINT via PhoneInfoga scanners."""
import asyncio
import json
import logging
import os
import re
import sys
from typing import Optional

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("phoneinfoga-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8503"))
mcp = FastMCP("PhoneInfoga MCP Server", instructions="Phone number OSINT using PhoneInfoga scanners (local, numverify, googlesearch, googlecse, ovh).")

ALL_SCANNERS = ["local", "numverify", "googlesearch", "googlecse", "ovh"]
BIN = os.environ.get("PHONEINFOGA_BIN", "phoneinfoga")


async def _run(args: list[str], timeout: int = 120, env_extra: dict | None = None) -> dict:
    import shutil
    binary = shutil.which(BIN) or "/usr/local/bin/phoneinfoga"
    if not os.path.isfile(binary):
        raise FileNotFoundError(f"phoneinfoga not found at {binary}")
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    proc = await asyncio.create_subprocess_exec(
        binary, *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        return {"stdout": "", "stderr": f"Timeout after {timeout}s", "return_code": -1}
    return {
        "stdout": stdout.decode("utf-8", errors="replace"),
        "stderr": stderr.decode("utf-8", errors="replace"),
        "return_code": proc.returncode or 0,
    }


@mcp.tool()
async def phoneinfoga_scan(
    phone_number: str,
    scanners: Optional[str] = None,
    timeout_seconds: int = 120,
) -> str:
    """Run PhoneInfoga scan on a phone number.

    Args:
        phone_number: Phone number to investigate (include country code, e.g. +1234567890).
        scanners: Comma-separated scanner names to use (local,numverify,googlesearch,googlecse,ovh). Leave empty for all.
        timeout_seconds: Max execution time in seconds.
    """
    if not phone_number or not phone_number.strip():
        return json.dumps({"error": "phone_number is required"})

    args = ["scan", "-n", phone_number.strip()]

    if scanners:
        wanted = [s.strip() for s in scanners.split(",") if s.strip()]
        invalid = [s for s in wanted if s not in ALL_SCANNERS]
        if invalid:
            return json.dumps({"error": f"Invalid scanners: {invalid}. Valid: {ALL_SCANNERS}"})
        disable = [s for s in ALL_SCANNERS if s not in wanted]
        for s in disable:
            args.extend(["-D", s])

    env_extra = {}
    for key in ["NUMVERIFY_API_KEY", "GOOGLE_API_KEY", "GOOGLECSE_CX"]:
        val = os.environ.get(key, "")
        if val:
            env_extra[key] = val

    logger.info("phoneinfoga_scan number=*%s scanners=%s", phone_number[-4:] if len(phone_number) > 4 else "***", scanners or "all")
    try:
        r = await _run(args, timeout=timeout_seconds, env_extra=env_extra if env_extra else None)
    except FileNotFoundError as e:
        return json.dumps({"error": str(e)})

    if r["return_code"] != 0:
        return json.dumps({"error": f"phoneinfoga failed (exit {r['return_code']})", "detail": (r["stderr"] or r["stdout"] or "").strip()})

    stdout = r["stdout"].strip()
    if not stdout:
        return json.dumps({"message": "No results", "stderr": r["stderr"].strip()})
    return stdout


@mcp.tool()
async def run_phoneinfoga(arguments: str, timeout_seconds: int = 120) -> str:
    """Run phoneinfoga with arbitrary CLI arguments.

    Args:
        arguments: Raw CLI arguments (e.g. 'scan -n +1234567890 -D googlesearch').
        timeout_seconds: Max execution time.
    """
    import shlex
    args = shlex.split(arguments) if arguments.strip() else ["-h"]
    logger.info("run_phoneinfoga arguments=%s", arguments)
    try:
        r = await _run(args, timeout=timeout_seconds)
    except FileNotFoundError as e:
        return json.dumps({"error": str(e)})
    if r["return_code"] != 0:
        return f"phoneinfoga failed (exit {r['return_code']}): {(r['stderr'] or r['stdout'] or '').strip()}"
    return (r["stdout"] or "").strip() or "Done."


if __name__ == "__main__":
    logger.info("Starting phoneinfoga-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
