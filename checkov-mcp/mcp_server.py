#!/usr/bin/env python3
"""Checkov MCP Server — Stateless Infrastructure as Code security scanning.

Clones a remote Git repository, runs Checkov to find misconfigurations,
returns the report, and securely deletes the repository.
"""

import asyncio
import json
import logging
import os
import shutil
import sys
import uuid
import shlex

from fastmcp import FastMCP
import hd_fetch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("checkov-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8272"))

mcp = FastMCP(
    "Checkov MCP Server",
    instructions=(
        "Stateless Infrastructure as Code (IaC) security scanning. "
        "Provide a public Git repository URL. The server will clone it, scan it with Checkov, and return the findings."
    ),
)

CHECKOV_BIN = os.environ.get("CHECKOV_BIN", "checkov")
WORKSPACE_DIR = "/tmp/checkov_workspace"


async def _clone_repo(repo_url: str, dest_path: str, timeout_seconds: int = 120) -> bool:
    """Clone a git repository with depth=1 for speed."""
    logger.info(f"Cloning repository from {repo_url}...")
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "--depth", "1", repo_url, dest_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
        if proc.returncode == 0 and os.path.exists(dest_path):
            return True
        logger.error(f"Git clone failed with exit code {proc.returncode}")
        return False
    except asyncio.TimeoutError:
        logger.error(f"Clone timed out after {timeout_seconds}s")
        if proc:
            proc.kill()
        return False
    except Exception as e:
        logger.error(f"Clone exception: {e}")
        return False


async def _run_command(cmd: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a command and return structured output."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
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
async def scan_remote_repo(
    repo_url: str,
    arguments: str = "--output json",
    timeout_seconds: int = 600,
) -> str:
    """Clone a Git repository, scan it with Checkov, and return the results.

    Args:
        repo_url: Public HTTPS Git repository URL to scan.
        arguments: Additional Checkov arguments (default: "--output json"). Do not provide the directory flag (-d).
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    if not shutil.which(CHECKOV_BIN):
        return json.dumps({"error": True, "message": f"{CHECKOV_BIN} binary not found in container."})

    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    temp_repo_path = os.path.join(WORKSPACE_DIR, f"repo_{uuid.uuid4().hex[:8]}")

    # 1. Clone the repository
    success = await _clone_repo(repo_url, temp_repo_path)
    if not success:
        return json.dumps({"error": True, "message": f"Failed to clone repository from {repo_url}."})

    # 2. Prepare Checkov command
    args = shlex.split(arguments) if arguments.strip() else []
    
    # Force Checkov not to exit with 1 if it finds vulnerabilities, so our wrapper doesn't panic
    if "--soft-fail" not in args:
        args.append("--soft-fail")

    cmd = [CHECKOV_BIN] + args + ["-d", temp_repo_path]
    logger.info(f"Running command: {' '.join(cmd)}")

    # 3. Execute Checkov
    result = await _run_command(cmd, timeout_seconds=timeout_seconds)

    # 4. Clean up the cloned repository immediately
    if os.path.exists(temp_repo_path):
        shutil.rmtree(temp_repo_path)
        logger.info(f"Cleaned up temporary repository: {temp_repo_path}")

    # If it completely crashed (e.g. invalid arguments), return the error
    if result["return_code"] != 0:
        return json.dumps({
            "error": True,
            "message": f"Checkov crashed (exit code {result['return_code']})",
            "detail": result["stderr"] or result["stdout"],
        }, indent=2)

    stdout = result["stdout"].strip()
    if not stdout:
        return json.dumps({"message": "Scan completed with no output."})

    # Checkov outputs JSON if requested. We try to parse it so the LLM gets a clean object.
    try:
        parsed_json = json.loads(stdout)
        return json.dumps(parsed_json, indent=2)
    except json.JSONDecodeError:
        return json.dumps({"raw_output": stdout}, indent=2)


def main():
    logger.info("Starting checkov-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()