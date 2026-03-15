import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from hd_logging import setup_logger

logger = setup_logger(__name__, log_file_path="logs/mcp_code_mode_mini_suite.log")


def _minijson(obj) -> str:
    return json.dumps(obj, separators=(",", ":"), default=str)


async def _run_step_1(bridge, timeout: int) -> dict:
    # 1) Whether the code execution even runs (no MCP servers).
    logger.info("[STEP1] start timeout=%s", timeout)
    code = "\n".join(
        [
            "import json",
            "out = {'step': 1, 'ok': True, 'msg': 'code execution ran'}",
            "print(json.dumps(out, separators=(',', ':')))",
        ]
    )
    try:
        result = await bridge.execute_code(code, servers=[], timeout=timeout)
        logger.info("[STEP1] ok stdout_len=%d stderr_len=%d", len(result.stdout or ""), len(result.stderr or ""))
        return {"step": 1, "success": True, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    finally:
        # Make step-by-step runs predictable (no long-lived sessions between steps).
        try:
            await bridge.close()
        except Exception:
            logger.error("[STEP1] close() failed", exc_info=True)


async def _run_step_2(bridge, timeout: int) -> dict:
    # 2) Are the MCP servers exposed (discovery vs loaded servers)?
    logger.info("[STEP2] start timeout=%s", timeout)
    await bridge.discover_servers()
    all_servers = list(getattr(bridge, "servers", {}).keys())
    logger.info("[STEP2] discovered servers=%s", all_servers)
    code = "\n".join(
        [
            "import json",
            "from mcp import runtime",
            "out = {}",
            "out['step'] = 2",
            "out['runtime_discovered_servers'] = list(runtime.discovered_servers())",
            "out['runtime_discovered_detailed'] = runtime.discovered_servers(detailed=True)",
            "out['runtime_loaded_servers'] = list(await runtime.list_servers())",
            "print(json.dumps(out, separators=(',', ':')))",
        ]
    )
    # run with no loaded servers; list_servers() should be empty, discovered_servers should include all discovered.
    try:
        result = await bridge.execute_code(code, servers=[], timeout=timeout)
        logger.info("[STEP2] ok stdout_len=%d stderr_len=%d", len(result.stdout or ""), len(result.stderr or ""))
        return {
            "step": 2,
            "success": True,
            "server_count": len(all_servers),
            "servers": all_servers,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    finally:
        try:
            await bridge.close()
        except Exception:
            logger.error("[STEP2] close() failed", exc_info=True)


async def _run_step_3(MCPBridge, servers: list[str], timeout: int) -> dict:
    # 3) Does the code execution level run as per documentation (load server -> list tools -> call one tool)?
    logger.info("[STEP3] start servers=%s timeout=%s", servers, timeout)
    checks = []
    for server in servers:
        entry = {"server": server, "status": "pending"}
        bridge = MCPBridge()
        try:
            # Important: each fresh bridge instance must discover servers before loading.
            await bridge.discover_servers()
            logger.info("[STEP3:%s] load_server()", server)
            # Fast pre-flight: ensure the server can be loaded at all.
            await bridge.load_server(server)
            meta = await bridge.get_cached_server_metadata(server)
            tools = meta.get("tools", []) or []
            entry["tool_count"] = len(tools)

            # Run a sandbox script that:
            # - confirms the server is loadable via runtime.list_servers()
            # - lists tools via RPC (this is the “LLM-like” path: host loads server, sandbox asks host to list tools)
            # - optionally calls one known lightweight tool where applicable
            code_lines = [
                "import json",
                "from mcp import runtime",
                f"target = {server!r}",
                "out = {'server': target}",
                "out['loaded_servers'] = list(await runtime.list_servers())",
                "try:",
                "  tools = await runtime.list_tools(target)",
                "  out['tool_count'] = len(tools) if isinstance(tools, (list, tuple)) else 0",
                "  out['tool_aliases'] = [t.get('alias') for t in (tools or []) if isinstance(t, dict) and t.get('alias')]",
                "except Exception as e:",
                "  out['tools_error'] = f\"{type(e).__name__}: {e}\"",
            ]
            if server == "hackerdogs-loggen-remote":
                code_lines.append("out['call'] = await mcp_hackerdogs_loggen_remote.get_supported_log_types()")
            elif server == "mitre-attack-remote":
                code_lines.append("out['call'] = await mcp_mitre_attack_remote.get_all_tactics(domain='enterprise', include_description=False)")
            elif server == "victorialogs":
                code_lines.append("out['call'] = await mcp_victorialogs.flags()")
            elif server.lower() == "playwright":
                # Avoid browser launch; listing tools is enough.
                code_lines.append("out['call'] = {'note':'listed tools only'}")
            elif server == "github":
                code_lines.append("out['call'] = {'note':'listed tools only'}")
            else:
                code_lines.append("out['call'] = {'note':'no server-specific call defined'}")
            code_lines.append("print(json.dumps(out, separators=(',', ':')))")
            code = "\n".join(code_lines)

            logger.info("[STEP3:%s] execute_code(run_python) ...", server)
            result = await bridge.execute_code(code, servers=[server], timeout=timeout)
            entry["stdout"] = result.stdout.strip()
            entry["stderr"] = result.stderr.strip()
            try:
                parsed = json.loads(entry["stdout"]) if entry["stdout"] else {}
            except Exception as parse_exc:
                entry["status"] = "fail"
                entry["error"] = f"stdout not json: {type(parse_exc).__name__}: {parse_exc}"
            else:
                entry["parsed"] = parsed
                # Treat any sandbox stderr as a failure signal (it usually means user code errored).
                if entry["stderr"]:
                    entry["status"] = "fail"
                    entry["error"] = "sandbox stderr not empty"
                elif parsed.get("tools_error"):
                    entry["status"] = "fail"
                    entry["error"] = parsed.get("tools_error")
                else:
                    entry["status"] = "pass"
        except Exception as exc:
            entry["status"] = "fail"
            entry["error"] = f"{type(exc).__name__}: {exc}"
            logger.error("[STEP3:%s] FAIL %s", server, entry["error"], exc_info=True)
        finally:
            try:
                await bridge.close()
            except Exception:
                logger.error("[STEP3:%s] close() failed", server, exc_info=True)
        checks.append(entry)
    return {"step": 3, "results": checks}


async def _main_async() -> int:
    parser = argparse.ArgumentParser(description="Mini test suite for MCP code execution mode (step-by-step).")
    parser.add_argument("--config", required=True, help="Path to mcp.json to use (Cursor format).")
    parser.add_argument("--timeout", type=int, default=20, help="Per-step timeout seconds for execute_code().")
    parser.add_argument(
        "--servers",
        default="",
        help="Comma-separated server names to test in step 3. Default: all discovered servers (excluding github if placeholder auth).",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    if not config_path.exists():
        print(_minijson({"status": "error", "error": f"config not found: {config_path}"}))
        return 2

    # Make imports work from repo checkout.
    repo_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_dir))

    import mcp_server_code_execution_mode as bridge_module
    from mcp_server_code_execution_mode import MCPBridge

    os.environ["MCP_SERVERS_CONFIG"] = str(config_path)

    # IMPORTANT:
    # The upstream bridge discovers MCP servers from many locations (Cursor, Claude, ~/MCPs, etc.).
    # For a deterministic "use THIS mcp.json" test, we temporarily disable all other config sources
    # so the env-provided MCP_SERVERS_CONFIG is the only catalog.
    original_sources = list(getattr(bridge_module, "CONFIG_SOURCES", []))
    bridge_module.CONFIG_SOURCES[:] = []
    try:
        bridge = MCPBridge()
    finally:
        # Keep sources disabled for the rest of this script run; restore at the end.
        pass

    out: dict = {"status": "ok", "config": str(config_path)}

    # Step 1
    out["step1"] = await _run_step_1(bridge, timeout=args.timeout)

    # Step 2
    out["step2"] = await _run_step_2(bridge, timeout=args.timeout)

    # Determine step 3 target servers
    # `discover_servers()` returns only "newly added" names, which can be confusing.
    # For reporting, use the authoritative list of all known servers.
    await bridge.discover_servers()
    discovered_names = list(getattr(bridge, "servers", {}).keys())
    if args.servers.strip():
        target_servers = [s.strip() for s in args.servers.split(",") if s.strip()]
    else:
        target_servers = list(discovered_names)

    # Skip github unless auth is set (avoid accidental secret prompts in logs)
    try:
        info = bridge.servers.get("github")
        auth = ""
        if info and getattr(info, "headers", None):
            auth = (info.headers or {}).get("Authorization", "")
        if "github" in target_servers and auth in {"", "__SET_VIA_SECRETS_STORE__", "__SECRET__"}:
            target_servers = [s for s in target_servers if s != "github"]
            out["note"] = "github skipped (Authorization missing/placeholder)"
    except Exception:
        pass

    out["step3"] = await _run_step_3(MCPBridge, servers=target_servers, timeout=max(10, args.timeout))

    print(_minijson(out))
    # fail if any server in step3 failed
    failures = [r for r in out["step3"]["results"] if r.get("status") == "fail"]
    rc = 1 if failures else 0
    # Restore config sources after run.
    bridge_module.CONFIG_SOURCES[:] = original_sources
    return rc


def main() -> None:
    raise SystemExit(asyncio.run(_main_async()))


if __name__ == "__main__":
    main()


