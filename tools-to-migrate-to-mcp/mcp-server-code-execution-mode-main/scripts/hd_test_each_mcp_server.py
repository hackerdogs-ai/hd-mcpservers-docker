"""
Test each MCP server from a Cursor-style mcp.json individually.

This is intended to mirror the product/LLM behaviour:
- Host loads an MCP server (stdio or URL) via the bridge
- Sandbox runs `run_python` with servers=[name]
- Sandbox calls `await runtime.list_tools(name)` (RPC) to verify exposure

Outputs a compact JSON summary to stdout and writes detailed logs via hd_logging.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from hd_logging import setup_logger


logger = setup_logger(__name__, log_file_path="logs/mcp_each_server_test.log")


def _minijson(obj: object) -> str:
    return json.dumps(obj, separators=(",", ":"), default=str)


def _load_dotenv_near(path: Path) -> None:
    """
    Load a .env file (if present) into os.environ without overriding existing vars.
    We keep this minimal to avoid adding dependencies.
    """
    # Try up to a few parent directories (repo root typically).
    for parent in [path.parent, *path.parents][:6]:
        env_path = parent / ".env"
        if not env_path.exists():
            continue
        try:
            for line in env_path.read_text().splitlines():
                raw = line.strip()
                if not raw or raw.startswith("#") or "=" not in raw:
                    continue
                k, v = raw.split("=", 1)
                k = k.strip()
                # Handle common .env patterns:
                # - quoted values
                # - line-continuation backslashes (we don't support multi-line, but we must drop the '\')
                # - inline comments (best-effort; only when unquoted)
                v = v.strip()
                # Drop trailing line-continuation marker
                if v.endswith("\\"):
                    v = v[:-1].rstrip()
                # Strip quotes
                if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
                    v = v[1:-1]
                # Best-effort inline comment strip for unquoted values
                if "#" in v and not (v.startswith("'") or v.startswith('"')):
                    v = v.split("#", 1)[0].rstrip()
                if k and k not in os.environ:
                    os.environ[k] = v
            logger.info("loaded .env from %s", env_path)
        except Exception:
            logger.error("failed loading .env from %s", env_path, exc_info=True)
        return


async def _test_one(server_name: str, config_path: Path, timeout: int) -> Dict[str, Any]:
    # Ensure the bridge package directory is on sys.path (scripts/ -> project root).
    bridge_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(bridge_root))

    import mcp_server_code_execution_mode as bridge_module  # type: ignore
    from mcp_server_code_execution_mode import MCPBridge, SandboxError  # type: ignore

    # Deterministic: only the provided config path.
    os.environ["MCP_SERVERS_CONFIG"] = str(config_path)
    bridge_module.CONFIG_SOURCES[:] = []

    bridge = MCPBridge()
    started = time.time()
    result: Dict[str, Any] = {
        "server": server_name,
        "status": "fail",
        "elapsed_s": None,
        "transport": None,
        "detail": "",
    }

    try:
        await bridge.discover_servers()
        info = bridge.servers.get(server_name)
        if not info:
            result["status"] = "fail"
            result["detail"] = "not found in discovered servers"
            return result

        result["transport"] = getattr(info, "transport", "unknown")

        # GitHub: allow placeholder in mcp.json, but require env injection (GITHUB_TOKEN).
        if server_name == "github":
            if not (os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_PAT") or os.environ.get("GH_TOKEN")):
                result["status"] = "fail"
                result["detail"] = "missing GITHUB_TOKEN (or GITHUB_PAT/GH_TOKEN) for github MCP Authorization"
                return result

        logger.info("[server:%s] load_server() start transport=%s", server_name, result["transport"])
        await asyncio.wait_for(bridge.load_server(server_name), timeout=timeout)
        logger.info("[server:%s] load_server() ok", server_name)

        # Minimal sandbox script: list tools via RPC (doc-recommended).
        code = "\n".join(
            [
                "import json",
                "from mcp import runtime",
                f"name = {server_name!r}",
                "out = {'server': name}",
                "out['loaded_servers'] = list(await runtime.list_servers())",
                "tools = await runtime.list_tools(name)",
                "out['tool_count'] = len(tools) if isinstance(tools, (list, tuple)) else 0",
                # Avoid dumping huge schemas; just show first 3 tool names
                "tool_names = []",
                "for t in (tools or [])[:3]:",
                "  if isinstance(t, dict) and t.get('name'):",
                "    tool_names.append(t.get('name'))",
                "out['tool_names_head'] = tool_names",
                "print(json.dumps(out, separators=(',', ':')))",
            ]
        )

        sandbox_res = await asyncio.wait_for(
            bridge.execute_code(code, servers=[server_name], timeout=timeout),
            timeout=timeout + 5,
        )

        stdout = (sandbox_res.stdout or "").strip()
        stderr = (sandbox_res.stderr or "").strip()
        if stderr:
            result["status"] = "fail"
            result["detail"] = f"sandbox stderr: {stderr[:500]}"
        else:
            try:
                parsed = json.loads(stdout) if stdout else {}
            except Exception:
                result["status"] = "fail"
                result["detail"] = f"stdout not json: {stdout[:200]}"
            else:
                result["status"] = "pass"
                result["tool_count"] = parsed.get("tool_count")
                result["tool_names_head"] = parsed.get("tool_names_head", [])
                result["detail"] = "ok"
        return result

    except SandboxError as exc:
        result["status"] = "fail"
        result["detail"] = f"SandboxError: {exc}"
        if getattr(exc, "stderr", ""):
            result["stderr"] = str(getattr(exc, "stderr", ""))[:1000]
        return result
    except asyncio.TimeoutError:
        result["status"] = "fail"
        result["detail"] = f"timeout after {timeout}s"
        return result
    except Exception as exc:
        result["status"] = "fail"
        result["detail"] = f"{type(exc).__name__}: {exc}"
        logger.error("[server:%s] unexpected error", server_name, exc_info=True)
        return result
    finally:
        result["elapsed_s"] = round(time.time() - started, 3)
        try:
            await bridge.close()
        except Exception:
            logger.error("[server:%s] bridge.close() failed", server_name, exc_info=True)


async def _main_async() -> int:
    parser = argparse.ArgumentParser(description="Test each MCP server in mcp.json individually.")
    parser.add_argument("--config", required=True, help="Path to Cursor-style mcp.json")
    parser.add_argument("--timeout", type=int, default=20, help="Per-server timeout seconds")
    parser.add_argument("--only", default="", help="Comma-separated server names to test (default: all)")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    if not config_path.exists():
        print(_minijson({"status": "error", "error": f"config not found: {config_path}"}))
        return 2

    _load_dotenv_near(config_path)

    cfg = json.loads(config_path.read_text())
    servers_cfg = cfg.get("mcpServers", {})
    if not isinstance(servers_cfg, dict) or not servers_cfg:
        print(_minijson({"status": "error", "error": "no mcpServers in config"}))
        return 2

    names = list(servers_cfg.keys())
    if args.only.strip():
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        names = [n for n in names if n in wanted]

    logger.info("starting per-server tests count=%d names=%s", len(names), names)

    results: List[Dict[str, Any]] = []
    for name in names:
        logger.info("==== TEST %s ====", name)
        if name == "github" and not os.environ.get("GITHUB_AUTHORIZATION"):
            # Try common schemes automatically so we don't guess or ask.
            # This does NOT print the token; it just reports status codes.
            scheme_results: List[Dict[str, Any]] = []
            for scheme in ["bearer", "token", "raw"]:
                os.environ["GITHUB_AUTH_SCHEME"] = scheme
                r = await _test_one(name, config_path, timeout=args.timeout)
                r["attempt_scheme"] = scheme
                scheme_results.append(r)
                if r.get("status") == "pass":
                    break
            results.extend(scheme_results)
            continue

        r = await _test_one(name, config_path, timeout=args.timeout)
        results.append(r)

    summary = {
        "status": "ok",
        "config": str(config_path),
        "count": len(results),
        "results": results,
        "pass": [r["server"] for r in results if r.get("status") == "pass"],
        "fail": [r["server"] for r in results if r.get("status") == "fail"],
        "skip": [r["server"] for r in results if r.get("status") == "skip"],
    }
    print(_minijson(summary))

    return 0 if not summary["fail"] else 1


def main() -> None:
    raise SystemExit(asyncio.run(_main_async()))


if __name__ == "__main__":
    main()


