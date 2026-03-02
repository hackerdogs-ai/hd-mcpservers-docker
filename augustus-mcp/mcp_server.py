#!/usr/bin/env python3
"""Augustus MCP Server — LLM adversarial vulnerability testing via MCP.

Wraps the augustus CLI (praetorian-inc/augustus) to expose LLM security
testing capabilities through the Model Context Protocol (MCP).

Augustus tests LLMs against adversarial attacks including prompt injection,
jailbreaks, encoding exploits, and data extraction using 210+ probes and
support for 28 LLM providers.
"""

import asyncio
import json
import logging
import os
import shutil
import sys
from typing import Optional

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("augustus-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8101"))

mcp = FastMCP(
    "Augustus MCP Server",
    instructions=(
        "LLM adversarial vulnerability testing. Tests LLMs against prompt "
        "injection, jailbreaks, encoding exploits, and data extraction using "
        "210+ probes and 28 LLM providers."
    ),
)

AUGUSTUS_BIN = os.environ.get("AUGUSTUS_BIN", "augustus")

LLM_PROVIDER_KEYS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "cohere": "COHERE_API_KEY",
    "azure": "AZURE_OPENAI_API_KEY",
    "bedrock": "AWS_ACCESS_KEY_ID",
    "vertex": "GOOGLE_APPLICATION_CREDENTIALS",
    "groq": "GROQ_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "together": "TOGETHER_API_KEY",
    "fireworks": "FIREWORKS_API_KEY",
    "deepinfra": "DEEPINFRA_API_KEY",
    "replicate": "REPLICATE_API_TOKEN",
}


def _check_provider_key(generator: str) -> str | None:
    """Return a warning if the API key for the given generator's provider is missing."""
    provider = generator.split(".")[0].lower() if "." in generator else generator.lower()
    if provider in ("test", "ollama", "ggml", "function", "rest"):
        return None
    env_var = LLM_PROVIDER_KEYS.get(provider)
    if env_var and not os.environ.get(env_var):
        return (
            f"{env_var} environment variable is not set. "
            f"Augustus needs it to test {generator}. "
            f"Set it before running scans against this provider."
        )
    return None


def _find_augustus() -> str:
    """Locate the augustus binary, raising a clear error if missing."""
    path = shutil.which(AUGUSTUS_BIN)
    if path is None:
        logger.error("augustus binary not found on PATH")
        raise FileNotFoundError(
            f"augustus binary not found. Ensure it is installed and available "
            f"on PATH, or set AUGUSTUS_BIN to the full path. "
            f"Install with: go install github.com/praetorian-inc/augustus/cmd/augustus@latest"
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 1800) -> dict:
    """Execute an augustus command and return structured output.

    Returns a dict with keys: stdout, stderr, return_code.
    """
    augustus = _find_augustus()
    cmd = [augustus] + args

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
        logger.error("Command timed out after %ds: %s", timeout_seconds, " ".join(cmd))
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout_seconds}s: {' '.join(cmd)}",
            "return_code": -1,
        }
    except Exception as exc:
        logger.error("Command execution failed: %s", exc)
        return {
            "stdout": "",
            "stderr": f"Failed to execute command: {exc}",
            "return_code": -1,
        }

    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")
    return {
        "stdout": stdout,
        "stderr": stderr,
        "return_code": proc.returncode,
    }


def _parse_timeout(timeout_str: str) -> int:
    """Convert a human-readable timeout (e.g. '30m', '1h') to seconds."""
    timeout_str = timeout_str.strip().lower()
    if timeout_str.endswith("h"):
        return int(timeout_str[:-1]) * 3600
    if timeout_str.endswith("m"):
        return int(timeout_str[:-1]) * 60
    if timeout_str.endswith("s"):
        return int(timeout_str[:-1])
    return int(timeout_str)


@mcp.tool()
async def scan_llm(
    generator: str,
    model: Optional[str] = None,
    probes: Optional[str] = None,
    probes_glob: Optional[str] = None,
    all_probes: bool = False,
    detector: Optional[str] = None,
    detectors_glob: Optional[str] = None,
    buff: Optional[str] = None,
    buffs_glob: Optional[str] = None,
    config_json: Optional[str] = None,
    output_format: str = "json",
    concurrency: int = 10,
    timeout: str = "30m",
    verbose: bool = False,
) -> str:
    """Run an adversarial vulnerability scan against an LLM.

    Tests the target LLM for prompt injection, jailbreaks, encoding exploits,
    and data extraction vulnerabilities using Augustus's library of 210+ probes.

    Requires the corresponding LLM provider API key to be set as an environment
    variable (e.g. OPENAI_API_KEY for OpenAI, ANTHROPIC_API_KEY for Anthropic).

    Args:
        generator: LLM provider generator name. Examples: 'openai.OpenAI',
            'anthropic.Anthropic', 'azure.AzureOpenAI', 'ollama.OllamaChat',
            'cohere.Cohere', 'groq.Groq', 'rest.Rest'.
        model: Model name to test (e.g. 'gpt-4', 'claude-3-opus-20240229',
            'llama3.2:3b'). Passed via --config if provided.
        probes: Comma-separated specific probe names (e.g. 'dan.Dan_11_0').
        probes_glob: Glob pattern for probes (e.g. 'dan.*,goodside.*').
        all_probes: Run all 210+ probes. Overrides probes/probes_glob.
        detector: Specific detector name (e.g. 'dan.DAN').
        detectors_glob: Glob pattern for detectors (e.g. 'dan.*').
        buff: Buff transformation to apply (e.g. 'encoding.Base64').
        buffs_glob: Glob pattern for buffs (e.g. 'encoding.*').
        config_json: JSON config string for the generator (e.g. '{"temperature":0.7}').
        output_format: Output format — 'json' (default), 'jsonl', or 'table'.
        concurrency: Max concurrent probe executions (default 10).
        timeout: Scan timeout (e.g. '30m', '1h'). Default '30m'.
        verbose: Enable verbose output for detailed scan progress.
    """
    logger.info("scan_llm called with generator=%s, model=%s", generator, model)

    key_warning = _check_provider_key(generator)
    if key_warning:
        logger.warning(key_warning)

    if model:
        if config_json:
            try:
                cfg = json.loads(config_json)
                cfg["model"] = model
                config_json = json.dumps(cfg)
            except json.JSONDecodeError:
                config_json = json.dumps({"model": model})
        else:
            config_json = json.dumps({"model": model})

    args = ["scan", generator]

    if all_probes:
        args.append("--all")
    elif probes:
        for p in probes.split(","):
            args.extend(["--probe", p.strip()])
    elif probes_glob:
        args.extend(["--probes-glob", probes_glob])

    if detector:
        args.extend(["--detector", detector])
    if detectors_glob:
        args.extend(["--detectors-glob", detectors_glob])
    if buff:
        args.extend(["--buff", buff])
    if buffs_glob:
        args.extend(["--buffs-glob", buffs_glob])
    if config_json:
        args.extend(["--config", config_json])
    if output_format:
        args.extend(["--format", output_format])
    if verbose:
        args.append("--verbose")

    args.extend(["--concurrency", str(concurrency)])
    args.extend(["--timeout", timeout])

    timeout_seconds = _parse_timeout(timeout) + 60

    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("augustus scan failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"Augustus scan failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"augustus {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()

    if output_format == "json":
        try:
            parsed = json.loads(stdout)
            return json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            pass

    return stdout if stdout else json.dumps({"message": "Scan completed with no output"})


@mcp.tool()
async def list_components() -> str:
    """List available Augustus components (probes, detectors, generators, harnesses, buffs).

    Returns the full list of available probes, detectors, generators, harnesses,
    and buffs that can be used with the scan_llm tool.
    """
    logger.info("list_components called")
    result = await _run_command(["list"])

    if result["return_code"] != 0:
        logger.warning("list_components failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"Failed to list components (exit code {result['return_code']})",
                "detail": error_detail.strip(),
            },
            indent=2,
        )

    return result["stdout"].strip() or json.dumps({"message": "No components listed"})


@mcp.tool()
async def get_version() -> str:
    """Get the installed Augustus version and build information."""
    logger.info("get_version called")
    result = await _run_command(["version"])

    if result["return_code"] != 0:
        logger.warning("get_version failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"Failed to get version (exit code {result['return_code']})",
                "detail": error_detail.strip(),
            },
            indent=2,
        )

    return result["stdout"].strip() or json.dumps({"message": "No version info returned"})


def main():
    logger.info("Starting augustus-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
