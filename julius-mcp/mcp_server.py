"""Julius MCP Server - LLM Service Fingerprinting via FastMCP."""

import json
import os
import subprocess
import shutil
import sys
import logging

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("julius-mcp")

mcp = FastMCP(
    "julius-mcp",
    instructions=(
        "MCP server for Julius - fingerprints 33+ LLM services (Ollama, vLLM, "
        "LiteLLM, HuggingFace TGI, LocalAI, LM Studio, NVIDIA NIM, and more) "
        "running on HTTP endpoints via active HTTP probing."
    ),
)

JULIUS_BIN = shutil.which("julius") or "julius"


def _run_julius(args: list[str], timeout: int = 30) -> dict:
    """Execute julius CLI and return structured result."""
    try:
        result = subprocess.run(
            [JULIUS_BIN] + args,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            logger.warning("julius exited with code %d: %s", result.returncode, stderr)

        parsed = None
        if output:
            try:
                parsed = json.loads(output)
            except json.JSONDecodeError:
                lines = output.splitlines()
                json_results = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        json_results.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
                if json_results:
                    parsed = json_results

        return {
            "success": result.returncode == 0,
            "output": parsed if parsed is not None else output,
            "stderr": stderr if stderr else None,
            "exit_code": result.returncode,
        }
    except FileNotFoundError:
        logger.error("julius binary not found at '%s'", JULIUS_BIN)
        return {
            "success": False,
            "output": None,
            "stderr": f"julius binary not found at '{JULIUS_BIN}'. Ensure julius is installed.",
            "exit_code": -1,
        }
    except subprocess.TimeoutExpired:
        logger.error("julius command timed out after %ds", timeout)
        return {
            "success": False,
            "output": None,
            "stderr": f"julius command timed out after {timeout}s",
            "exit_code": -1,
        }
    except Exception as exc:
        logger.error("julius command failed: %s", exc)
        return {
            "success": False,
            "output": None,
            "stderr": str(exc),
            "exit_code": -1,
        }


@mcp.tool()
def probe_targets(
    targets: str,
    output_format: str = "json",
    concurrency: int = 10,
    timeout: int = 5,
    quiet: bool = False,
    verbose: bool = False,
) -> dict:
    """Probe one or more target URLs to fingerprint which LLM service is running.

    Julius identifies 33+ LLM services by sending crafted HTTP probes and
    matching response signatures. Detects self-hosted servers (Ollama, vLLM,
    LiteLLM, LocalAI, HuggingFace TGI, LM Studio, NVIDIA NIM, llama.cpp,
    Aphrodite, FastChat, GPT4All, KoboldCpp, TabbyAPI, etc.), gateway/proxy
    services (LiteLLM, Kong AI Gateway, Envoy AI Gateway), RAG platforms
    (AnythingLLM, Dify, Flowise, LibreChat, Open WebUI, etc.), and
    OpenAI-compatible endpoints.

    No API keys required — Julius only sends standard HTTP requests.

    Args:
        targets: Space-separated target URLs (e.g. "http://host:11434 https://host2:8000").
        output_format: Output format — "json" (default) or "jsonl".
        concurrency: Number of concurrent probes. Default 10.
        timeout: Per-probe HTTP timeout in seconds. Default 5.
        quiet: Suppress informational output, only return matches.
        verbose: Enable verbose output for debugging.

    Returns:
        Dictionary with probe results including identified service, specificity
        score, category, and discovered models.
    """
    logger.info("probe_targets called with targets=%s", targets)
    args = ["probe"]
    args.extend(targets.split())

    if output_format in ("json", "jsonl"):
        args.extend(["-o", output_format])

    args.extend(["-c", str(concurrency)])
    args.extend(["-t", str(timeout)])

    if quiet:
        args.append("-q")
    if verbose:
        args.append("-v")

    overall_timeout = max(timeout * concurrency, 30) + 10
    return _run_julius(args, timeout=overall_timeout)


@mcp.tool()
def list_probes() -> dict:
    """List all available probe definitions that Julius can use.

    Returns the set of built-in probes Julius uses to fingerprint LLM services,
    including probe names, descriptions, and the services they detect.

    Returns:
        Dictionary with available probe definitions.
    """
    logger.info("list_probes called")
    return _run_julius(["list"])


@mcp.tool()
def validate_probes(path: str) -> dict:
    """Validate custom probe definition files.

    Checks that a probe definition file (YAML/JSON) is well-formed and
    contains valid probe configurations that Julius can execute.

    Args:
        path: File path to the probe definition file to validate.

    Returns:
        Dictionary with validation results.
    """
    logger.info("validate_probes called with path=%s", path)
    return _run_julius(["validate", path])


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    port = int(os.environ.get("MCP_PORT", "8100"))
    logger.info("Starting julius-mcp server (transport=%s, port=%s)", transport, port)

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
