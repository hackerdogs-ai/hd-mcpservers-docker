import argparse
import asyncio
import json
import os
import sys
from pathlib import Path


def _minijson(obj) -> str:
    return json.dumps(obj, separators=(",", ":"), default=str)


async def _run() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke test the vendored mcp-server-code-execution-mode bridge against an mcp.json catalog."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to mcp.json (Cursor-format: {mcpServers:{...}}).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Per-server timeout in seconds for the run_python call.",
    )
    parser.add_argument(
        "--max-servers",
        type=int,
        default=0,
        help="Optional limit (0 = no limit). Useful for quick iteration.",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    if not config_path.exists():
        print(_minijson({"status": "error", "error": f"config not found: {config_path}"}))
        return 2

    # Ensure we can import the vendored module from this repo checkout.
    repo_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_dir))

    from mcp_server_code_execution_mode import MCPBridge

    # Use the bridge's native env var override path so discovery is deterministic.
    os.environ["MCP_SERVERS_CONFIG"] = str(config_path)

    bridge = MCPBridge()
    discovered = await bridge.discover_servers()

    server_names = list(discovered.keys())
    if args.max_servers and args.max_servers > 0:
        server_names = server_names[: args.max_servers]

    results = []
    for name in server_names:
        entry = {
            "server": name,
            "description": discovered.get(name, ""),
            "status": "pending",
        }
        try:
            info = bridge.servers.get(name)
            entry["transport"] = getattr(info, "transport", "unknown") if info else "unknown"
            entry["url"] = getattr(info, "url", None) if info else None

            # GitHub is expected to require auth; skip if Authorization looks placeholder.
            if info and getattr(info, "headers", None):
                auth = (info.headers or {}).get("Authorization", "")
                if auth in {"", "__SET_VIA_SECRETS_STORE__", "__SECRET__", "__SET_VIA_SECRETS_STORE__"}:
                    entry["status"] = "skipped"
                    entry["reason"] = "auth header missing/placeholder"
                    results.append(entry)
                    continue

            await bridge.load_server(name)
            metadata = await bridge.get_server_metadata(name)
            entry["tool_count"] = len(metadata.get("tools", []) or [])

            # Exercise the LLM-like path: run a sandbox script that lists servers and tools,
            # then (optionally) calls a tool if we know one for this server.
            smoke_code_lines = [
                "import json",
                "from mcp import runtime",
                "out = {'server': '"
                + name.replace("'", "\\'")
                + "', 'servers': list(await runtime.list_servers())}",
                "out['tools'] = [t['alias'] for t in runtime.list_tools_sync('"
                + name.replace("'", "\\'")
                + "')]",
            ]

            # Minimal deterministic tool calls for known servers (best-effort).
            if name == "victorialogs":
                smoke_code_lines.append(
                    "out['call'] = await mcp_victorialogs.flags()"
                )
            elif name == "mitre-attack-remote":
                smoke_code_lines.append(
                    "out['call'] = await mcp_mitre_attack_remote.get_all_tactics(domain='enterprise', include_description=False)"
                )
            elif name == "hackerdogs-loggen-remote":
                smoke_code_lines.append(
                    "out['call'] = await mcp_hackerdogs_loggen_remote.get_supported_log_types()"
                )
            elif name.lower() == "playwright":
                # Playwright MCP varies; try listing tools only (avoid browser launch).
                smoke_code_lines.append("out['call'] = {'note':'listed tools only'}")
            elif name == "github":
                smoke_code_lines.append("out['call'] = {'note':'auth present; listed tools only'}")
            else:
                smoke_code_lines.append("out['call'] = {'note':'no server-specific call defined'}")

            smoke_code_lines.append("print(json.dumps(out, separators=(',', ':')))")
            smoke_code = "\n".join(smoke_code_lines)

            result = await bridge.execute_code(
                smoke_code,
                servers=[name],
                timeout=args.timeout,
            )

            entry["sandbox_success"] = bool(getattr(result, "success", False))
            entry["sandbox_exit_code"] = int(getattr(result, "exit_code", 1))
            entry["stdout"] = getattr(result, "stdout", "")
            entry["stderr"] = getattr(result, "stderr", "")
            entry["status"] = "pass" if entry["sandbox_success"] else "fail"
        except Exception as exc:
            entry["status"] = "fail"
            entry["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            results.append(entry)

    summary = {
        "status": "ok",
        "discovered_count": len(discovered),
        "tested_count": len(server_names),
        "results": results,
    }
    print(_minijson(summary))
    return 0 if all(r["status"] in {"pass", "skipped"} for r in results) else 1


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()


