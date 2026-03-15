"""
Certgraph Tool for LangChain Agents

This module provides a LangChain tool wrapper around `certgraph`:
https://github.com/lanrat/certgraph

Certgraph builds a graph of certificate relationships for a given host, using
drivers such as:
- http   (direct TLS fetch; most reliable)
- crtsh  (certificate transparency; can be expansive and occasionally flaky)
- smtp, censys

This implementation follows Hackerdogs OSINT tool standards:
- Docker-only execution (no host binaries)
- ToolRuntime-aware configuration (optional defaults)
- safe_log_* logging and defensive error handling
- JSON output returned to the agent (certgraph -json)

Environment variables (optional; provided via ToolRuntime):
- CERTGRAPH_DOCKER_PLATFORM: Force docker platform (e.g., "linux/amd64" on Apple Silicon)
- CERTGRAPH_DEFAULT_DRIVER: Default driver list when caller doesn't specify.
  - If empty / not provided, the tool defaults to "http" only.
  - If provided, it must be a comma-separated list from: http, crtsh, smtp, censys
  - http is always forced to be present.
- CERTGRAPH_DEFAULT_DEPTH: Default BFS depth when caller doesn't specify (default: 1)
- CENSYS_APPID: Censys AppID (required when using driver "censys")
- CENSYS_SECRET: Censys API Secret (required when using driver "censys")

Notes:
- certgraph image on GHCR may not publish linux/arm64. On Apple Silicon, use
  platform="linux/amd64" (this tool auto-selects when machine is arm64/aarch64).
"""

from __future__ import annotations

import json
import platform as _platform
from typing import Any, Dict, Optional

from langchain.tools import tool, ToolRuntime
from hd_logging import setup_logger

from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug
from shared.modules.tools.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/certgraph_tool.log")


def _check_docker_available() -> bool:
    """Check if Docker is available for running certgraph in container."""
    client = get_docker_client()
    if client is None:
        safe_log_debug(logger, "[certgraph] Docker client is None")
    is_available = client.docker_available if client else False
    safe_log_debug(logger, "[certgraph] Docker availability check", docker_available=is_available)
    return is_available


def _get_runtime_env(runtime: ToolRuntime, key: str) -> Optional[str]:
    """
    Get an environment variable from ToolRuntime state.

    Resolution order:
    1) runtime.state["environment_variables"][<instance>][key]
    2) runtime.state["environment_variables"][key] (flat dict fallback)
    3) runtime.state["api_keys"][key] (fallback used by other tools)
    """
    try:
        if not runtime or not getattr(runtime, "state", None):
            return None

        env_vars = runtime.state.get("environment_variables", {})
        if isinstance(env_vars, dict):
            # Preferred: instance-scoped mapping
            for instance_name, instance_env in env_vars.items():
                if isinstance(instance_env, dict) and key in instance_env and instance_env.get(key):
                    safe_log_debug(
                        logger,
                        "[certgraph] Found runtime env var",
                        key=key,
                        instance_name=instance_name,
                    )
                    return str(instance_env.get(key))

            # Fallback: flat dict
            if key in env_vars and env_vars.get(key):
                safe_log_debug(logger, "[certgraph] Found runtime env var (flat)", key=key)
                return str(env_vars.get(key))

        # Fallback used across other tools: runtime.state["api_keys"][KEY]
        api_keys = runtime.state.get("api_keys", {})
        if isinstance(api_keys, dict) and key in api_keys and api_keys.get(key):
            safe_log_debug(logger, "[certgraph] Found runtime api key", key=key)
            return str(api_keys.get(key))
    except Exception:
        # Never hard-fail env resolution
        return None

    return None


def _default_platform(runtime: ToolRuntime) -> Optional[str]:
    """
    Decide docker --platform for certgraph.

    - If runtime provides CERTGRAPH_DOCKER_PLATFORM, use it.
    - Else, on arm64/aarch64 (common on macOS Apple Silicon), default to linux/amd64.
    - Else, let Docker decide (None).
    """
    forced = _get_runtime_env(runtime, "CERTGRAPH_DOCKER_PLATFORM")
    if forced:
        return forced

    machine = (_platform.machine() or "").lower()
    if machine in {"arm64", "aarch64"}:
        return "linux/amd64"

    return None


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _extract_json_from_text(text: str) -> Optional[Any]:
    """
    Best-effort JSON extraction.

    certgraph normally prints JSON to stdout, but in some cases output can be empty
    or mixed with logs. This tries:
    1) json.loads(text) if text looks like JSON
    2) json.loads(text[first '{' ... last '}']) if braces exist
    """
    if not text or not isinstance(text, str):
        return None

    s = text.strip()
    if not s:
        return None

    # Fast path: direct JSON
    if s.startswith("{") or s.startswith("["):
        try:
            return json.loads(s)
        except Exception:
            pass

    # Mixed output: try extracting a JSON object
    try:
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = s[start : end + 1]
            return json.loads(candidate)
    except Exception:
        return None

    return None


def _redact_secrets_in_certgraph_output(parsed: Any) -> Any:
    """
    Redact any secrets from certgraph JSON output before returning it to the agent/UI.

    certgraph includes the invoked command line in output:
      output["certgraph"]["command"] == "certgraph ... -censys-secret <secret> ..."
    We must never return secrets verbatim.
    """
    try:
        if not isinstance(parsed, dict):
            return parsed

        cg = parsed.get("certgraph")
        if not isinstance(cg, dict):
            return parsed

        cmd = cg.get("command")
        if isinstance(cmd, str) and cmd:
            # Redact value following -censys-secret / --censys-secret
            tokens = cmd.split()
            redact_flags = {"-censys-secret", "--censys-secret"}
            out_tokens: list[str] = []
            i = 0
            while i < len(tokens):
                t = tokens[i]
                out_tokens.append(t)
                if t in redact_flags and i + 1 < len(tokens):
                    out_tokens.append("***REDACTED***")
                    i += 2
                    continue
                i += 1
            cg["command"] = " ".join(out_tokens)
            parsed["certgraph"] = cg

        return parsed
    except Exception:
        return parsed


def _parse_driver_list(driver: str) -> Optional[str]:
    """
    Validate and normalize certgraph driver list.

    certgraph expects a comma-separated string for -driver, e.g. "http,crtsh".
    """
    if not driver or not isinstance(driver, str):
        return None

    raw_parts = [p.strip() for p in driver.split(",")]
    parts = [p for p in raw_parts if p]
    if not parts:
        return None

    allowed = {"crtsh", "smtp", "censys", "http"}
    for p in parts:
        if p not in allowed:
            return None

    # Keep order but remove duplicates
    seen = set()
    normalized: list[str] = []
    for p in parts:
        if p in seen:
            continue
        seen.add(p)
        normalized.append(p)

    # Requirement: http must always be present.
    # If caller didn't include it, prepend it.
    if "http" not in seen:
        normalized = ["http"] + normalized

    return ",".join(normalized)


@tool
def certgraph_json(
    runtime: ToolRuntime,
    host: str,
    driver: Optional[str] = None,
    depth: Optional[int] = None,
    timeout: int = 180,
) -> str:
    """
    Build a certificate relationship graph for a host and return JSON output.

    This tool runs `certgraph -json` in Docker and returns certgraph's JSON graph.

    Recommended defaults:
    - driver="http" (direct TLS fetch; stable)
    - depth=1 (keeps output manageable; increase cautiously)

    Args:
        runtime: ToolRuntime instance (automatically injected).
        host: Target hostname (e.g., "example.com", "github.com").
        driver: Driver(s) to use. Common values: "http", "crtsh".
                You can pass multiple as a comma-separated string, e.g. "http,crtsh".
        depth: BFS depth (default: 1). Higher values can explode output size.
        timeout: Docker execution timeout in seconds (default: 180).

    Returns:
        - On success: the certgraph JSON graph (string)
        - On error: JSON object with status=error and message
    """
    try:
        safe_log_info(
            logger,
            "[certgraph_json] Starting",
            host=host,
            driver=driver,
            depth=depth,
            timeout=timeout,
        )

        # Validate inputs
        if not host or not isinstance(host, str) or len(host.strip()) == 0:
            error_msg = "host must be a non-empty string"
            safe_log_error(logger, "[certgraph_json] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})

        host = host.strip()

        if timeout < 1 or timeout > 3600:
            error_msg = "timeout must be between 1 and 3600 seconds"
            safe_log_error(logger, "[certgraph_json] Validation failed", error_msg=error_msg, timeout=timeout)
            return json.dumps({"status": "error", "message": error_msg})

        if not _check_docker_available():
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Ensure Docker is running: docker ps\n"
                "2. Image will be pulled automatically: ghcr.io/lanrat/certgraph\n"
                "3. On Apple Silicon, set CERTGRAPH_DOCKER_PLATFORM=linux/amd64 if needed"
            )
            safe_log_error(logger, "[certgraph_json] Docker not available", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})

        # ToolRuntime-configurable defaults
        # If CERTGRAPH_DEFAULT_DRIVER is missing/blank, default to http-only.
        default_driver_env = _get_runtime_env(runtime, "CERTGRAPH_DEFAULT_DRIVER")
        default_driver = (default_driver_env.strip() if isinstance(default_driver_env, str) else "") or "http"
        default_depth = _coerce_int(_get_runtime_env(runtime, "CERTGRAPH_DEFAULT_DEPTH"), 1)

        effective_driver_raw = (driver or default_driver).strip()
        effective_driver = _parse_driver_list(effective_driver_raw)
        if not effective_driver:
            error_msg = "driver must be a comma-separated list of: http, crtsh, smtp, censys"
            safe_log_error(
                logger,
                "[certgraph_json] Validation failed",
                error_msg=error_msg,
                driver=effective_driver_raw,
            )
            return json.dumps({"status": "error", "message": error_msg})

        effective_depth = int(depth) if depth is not None else default_depth

        # Keep depth within a sane bound to avoid runaway graphs
        if effective_depth < 0 or effective_depth > 10:
            error_msg = "depth must be between 0 and 10"
            safe_log_error(logger, "[certgraph_json] Validation failed", error_msg=error_msg, depth=effective_depth)
            return json.dumps({"status": "error", "message": error_msg})

        docker_platform = _default_platform(runtime)
        safe_log_debug(
            logger,
            "[certgraph_json] Execution plan",
            effective_driver=effective_driver,
            effective_depth=effective_depth,
            docker_platform=docker_platform if docker_platform else "default",
        )

        args = ["-json", "-depth", str(effective_depth), "-driver", effective_driver]

        # Optional: Censys credentials
        # If driver list includes censys but keys are missing/empty, drop censys from the driver list
        # so defaults can safely include all drivers without breaking execution.
        driver_parts = [p.strip() for p in effective_driver.split(",") if p.strip()]
        driver_set = set(driver_parts)
        if "censys" in driver_set:
            censys_appid = _get_runtime_env(runtime, "CENSYS_APPID")
            censys_secret = _get_runtime_env(runtime, "CENSYS_SECRET")
            if censys_appid and censys_secret:
                # IMPORTANT: never log secrets; only pass to container
                args.extend(["-censys-appid", str(censys_appid), "-censys-secret", str(censys_secret)])
            else:
                # Remove censys from effective driver list
                new_driver_parts = [p for p in driver_parts if p != "censys"]
                effective_driver = ",".join(new_driver_parts) if new_driver_parts else "http"
                safe_log_info(
                    logger,
                    "[certgraph_json] Censys driver requested but credentials missing; skipping censys",
                    host=host,
                    effective_driver=effective_driver,
                )
                # Update the args to reflect the updated driver list
                # args structure: ["-json","-depth",X,"-driver",DRIVERS]
                try:
                    driver_idx = args.index("-driver")
                    args[driver_idx + 1] = effective_driver
                except Exception:
                    pass

        args.append(host)

        docker_result = execute_in_docker(
            "certgraph",
            args,
            timeout=timeout,
            platform=docker_platform,
        )

        if docker_result.get("status") != "success":
            # Prefer structured message, then stderr
            error_detail = (
                docker_result.get("message")
                or (docker_result.get("stderr") if docker_result.get("stderr") else None)
                or "Unknown error"
            )
            error_msg = f"certgraph failed: {error_detail}"
            safe_log_error(
                logger,
                "[certgraph_json] Execution failed",
                exc_info=True,
                error=error_msg,
                host=host,
                driver=effective_driver,
                depth=effective_depth,
            )
            return json.dumps(
                {
                    "status": "error",
                    "message": error_msg,
                    "stderr": docker_result.get("stderr", ""),
                    "returncode": docker_result.get("returncode", -1),
                }
            )

        stdout = docker_result.get("stdout", "") or ""
        stderr = docker_result.get("stderr", "") or ""

        # Validate JSON output
        parsed = _extract_json_from_text(stdout)
        # Some runs can emit JSON to stderr (or emit only stderr).
        if parsed is None:
            parsed = _extract_json_from_text(stderr)

        if parsed is None:
            error_msg = "certgraph returned non-JSON output: empty or unparsable output"
            safe_log_error(
                logger,
                "[certgraph_json] JSON parse failed",
                exc_info=True,
                error=error_msg,
                host=host,
                output_length=len(stdout),
                stderr_length=len(stderr),
            )
            return json.dumps(
                {
                    "status": "error",
                    "message": error_msg,
                    "raw_stdout": stdout[:4000],
                    "raw_stderr": stderr[:4000],
                }
            )

        parsed = _redact_secrets_in_certgraph_output(parsed)

        # If Censys is requested alongside other drivers, certgraph v0.1.2 can emit a Censys
        # error (e.g., HTTP 404 on the Censys endpoint) and end up returning an effectively
        # empty graph (depth=0, links=[], nodes~1). In that case, fall back to re-running
        # without the censys driver so http/crtsh/smtp results still return meaningful data.
        try:
            driver_set = set([p.strip() for p in effective_driver.split(",") if p.strip()])
            has_censys = "censys" in driver_set
            has_other = len(driver_set - {"censys"}) > 0
            nodes_len = len(parsed.get("nodes", [])) if isinstance(parsed, dict) else 0
            links_len = len(parsed.get("links", [])) if isinstance(parsed, dict) else 0
            depth_val = parsed.get("depth") if isinstance(parsed, dict) else None

            censys_error_hint = ("censys" in (stderr or "").lower()) and ("error on request" in (stderr or "").lower())
            graph_effectively_empty = (links_len == 0) and (nodes_len <= 1) and (depth_val in (0, "0", None))

            if has_censys and has_other and (censys_error_hint or graph_effectively_empty):
                fallback_driver = ",".join([p for p in effective_driver.split(",") if p.strip() and p.strip() != "censys"])
                fallback_driver = _parse_driver_list(fallback_driver) or "http"
                safe_log_info(
                    logger,
                    "[certgraph_json] Censys caused empty/failed graph; retrying without censys",
                    host=host,
                    original_driver=effective_driver,
                    fallback_driver=fallback_driver,
                )

                fallback_args = ["-json", "-depth", str(effective_depth), "-driver", fallback_driver, host]
                fallback_result = execute_in_docker(
                    "certgraph",
                    fallback_args,
                    timeout=timeout,
                    platform=docker_platform,
                )
                fb_stdout = fallback_result.get("stdout", "") or ""
                fb_stderr = fallback_result.get("stderr", "") or ""
                fb_parsed = _extract_json_from_text(fb_stdout) or _extract_json_from_text(fb_stderr)
                if isinstance(fb_parsed, dict):
                    fb_parsed = _redact_secrets_in_certgraph_output(fb_parsed)
                    parsed = fb_parsed
        except Exception:
            # Never break success path on fallback heuristics
            pass

        safe_log_info(
            logger,
            "[certgraph_json] Complete",
            host=host,
            driver=effective_driver,
            depth=effective_depth,
            output_length=len(stdout),
            stderr_length=len(stderr),
        )

        # Return the graph JSON itself (not wrapped) to keep downstream handling simple.
        return json.dumps(parsed, indent=2)

    except Exception as e:
        safe_log_error(logger, "[certgraph_json] Error", exc_info=True, error=str(e), host=host if "host" in locals() else None)
        return json.dumps({"status": "error", "message": f"certgraph_json failed: {str(e)}"})


