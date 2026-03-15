import io
import json
import os
import sys
import unittest
from typing import Any, Dict, List, Sequence, TypedDict, cast

from mcp_server_code_execution_mode import RootlessContainerSandbox


class ToolMetadata(TypedDict):
    name: str
    alias: str
    description: str
    input_schema: Dict[str, object]


class ServerMetadata(TypedDict):
    name: str
    alias: str
    tools: List[ToolMetadata]
    cwd: str


class RuntimeResult(TypedDict):
    calls: List[Dict[str, object]]
    rpc_payloads: List[Dict[str, object]]
    stdout: str
    stderr: str
    sandbox_exports: Dict[str, object] | None
    runtime_module: Any | None
    mcp_package: Any | None
    demo_module: Any | None


def _default_metadata() -> List[ServerMetadata]:
    return [
        {
            "name": "demo-server",
            "alias": "demo_server",
            "tools": [
                {
                    "name": "list_things",
                    "alias": "list_things",
                    "description": "List available things",
                    "input_schema": {"type": "object", "properties": {}},
                }
            ],
            # Optional field that some servers can declare to indicate the working directory
            # the host will start the server in. Tests may rely on this value to validate
            # that runtime.describe_server(name) returns the metadata including 'cwd'.
            "cwd": "/home/demo/projects",
        }
    ]


def _select_tool_metadata(
    server_info: ServerMetadata, target: str | None
) -> ToolMetadata:
    tools = server_info["tools"]
    if not tools:
        raise AssertionError("Server metadata must include at least one tool")
    if target is not None:
        normalized = str(target).lower()
        for tool in tools:
            if normalized in {tool["alias"].lower(), tool["name"].lower()}:
                return tool
    return tools[0]


def _format_doc(
    server_info: ServerMetadata, tool_spec: ToolMetadata, detail: str
) -> Dict[str, object]:
    doc: Dict[str, object] = {
        "server": server_info["name"],
        "serverAlias": server_info["alias"],
        "tool": tool_spec["name"],
        "toolAlias": tool_spec["alias"],
    }
    description = tool_spec["description"]
    if description:
        doc["description"] = description
    if detail == "full":
        doc["inputSchema"] = tool_spec["input_schema"]
    return doc


def _run_entrypoint(
    user_code: str, metadata: Sequence[ServerMetadata] | None = None
) -> RuntimeResult:
    metadata_list = list(metadata) if metadata is not None else _default_metadata()

    dummy_sandbox = RootlessContainerSandbox.__new__(RootlessContainerSandbox)

    entrypoint = RootlessContainerSandbox._render_entrypoint(
        dummy_sandbox,
        cast(Sequence[Dict[str, object]], metadata_list),
        {metadata_list[0]["name"]: "Description"},
    )

    calls: List[Dict[str, object]] = []
    rpc_payloads: List[Dict[str, object]] = []
    stdout_chunks: List[str] = []
    stderr_chunks: List[str] = []

    read_fd, write_fd = os.pipe()
    reader = os.fdopen(read_fd, "rb", buffering=0)
    writer = os.fdopen(write_fd, "wb", buffering=0)
    stdin_wrapper = io.TextIOWrapper(reader, encoding="utf-8")

    # Write the execute command
    execute_cmd = {"type": "execute", "code": user_code}
    writer.write(json.dumps(execute_cmd).encode("utf-8") + b"\n")
    writer.flush()

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    original___stdout__ = sys.__stdout__
    original_stdin = sys.stdin

    def _send_response(message_id: int, payload: Dict[str, object]) -> None:
        response = {
            "type": "rpc_response",
            "id": message_id,
            "success": payload.get("success", True),
            "payload": payload,
        }
        if not response["success"]:
            response["error"] = payload.get("error", "RPC error")
        writer.write(
            json.dumps(response, separators=(",", ":")).encode("utf-8") + b"\n"
        )
        writer.flush()

    class _StdoutCapture:
        def __init__(self) -> None:
            self._buffer = ""

        def write(self, data: str) -> None:
            self._buffer += data
            while "\n" in self._buffer:
                line, self._buffer = self._buffer.split("\n", 1)
                if not line:
                    continue
                message = json.loads(line)
                calls.append(message)
                msg_type = message.get("type")
                if msg_type == "stdout":
                    stdout_chunks.append(str(message.get("data", "")))
                elif msg_type == "stderr":
                    stderr_chunks.append(str(message.get("data", "")))
                elif msg_type == "rpc_request":
                    payload = message.get("payload", {})
                    rpc_payloads.append(payload)
                    req_type = payload.get("type")
                    message_id = message.get("id")
                    server_info = metadata_list[0]
                    if req_type == "call_tool":
                        _send_response(message_id, {"success": True, "result": ["ok"]})
                    elif req_type == "list_tools":
                        _send_response(
                            message_id, {"success": True, "tools": server_info["tools"]}
                        )
                    elif req_type == "list_servers":
                        _send_response(
                            message_id,
                            {"success": True, "servers": [server_info["name"]]},
                        )
                    elif req_type == "query_tool_docs":
                        detail = str(payload.get("detail", "summary")).lower()
                        if "tool" in payload and payload.get("tool") is not None:
                            selected = _select_tool_metadata(
                                server_info, str(payload.get("tool"))
                            )
                            docs = [_format_doc(server_info, selected, detail)]
                        else:
                            docs = [
                                _format_doc(server_info, spec, detail)
                                for spec in server_info["tools"]
                            ]
                        _send_response(message_id, {"success": True, "docs": docs})
                    elif req_type == "search_tool_docs":
                        detail = str(payload.get("detail", "summary")).lower()
                        limit = payload.get("limit")
                        tools = [
                            _format_doc(server_info, spec, detail)
                            for spec in server_info["tools"]
                        ]
                        if isinstance(limit, int) and limit > 0:
                            tools = tools[:limit]
                        _send_response(message_id, {"success": True, "results": tools})
                    else:
                        raise AssertionError(f"Unexpected RPC payload: {payload}")
                elif msg_type == "execution_done":
                    try:
                        writer.close()
                    except ValueError:
                        pass
                else:
                    raise AssertionError(f"Unexpected message type: {message}")

        def flush(self) -> None:  # pragma: no cover - compatibility shim
            return None

    fake_stdout = _StdoutCapture()

    namespace: dict[str, object] = {"__name__": "__main__"}
    original_modules = {name for name in sys.modules if name.startswith("mcp")}
    sandbox_exports: Dict[str, object] | None = None
    mcp_package: Any | None = None
    runtime_module: Any | None = None
    demo_module: Any | None = None

    try:
        sys.__stdout__ = fake_stdout  # type: ignore
        sys.stdin = stdin_wrapper
        try:
            exec(entrypoint, namespace)
        except SystemExit:
            pass
        sandbox_exports = namespace.get("mcp_servers")  # type: ignore[assignment]
        mcp_package = namespace.get("mcp")
        demo_module = sys.modules.get("mcp.servers.demo_server")
        runtime_module = sys.modules.get("mcp.runtime")
    finally:
        sys.__stdout__ = original___stdout__  # type: ignore
        sys.stdin = original_stdin
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        try:
            writer.close()
        except ValueError:
            pass
        stdin_wrapper.close()
        for name in list(sys.modules):
            if name.startswith("mcp") and name not in original_modules:
                sys.modules.pop(name, None)

    return {
        "calls": calls,
        "rpc_payloads": rpc_payloads,
        "stdout": "".join(stdout_chunks),
        "stderr": "".join(stderr_chunks),
        "sandbox_exports": sandbox_exports,
        "runtime_module": runtime_module,
        "mcp_package": mcp_package,
        "demo_module": demo_module,
    }


class EntryPointGenerationTests(unittest.TestCase):
    def test_generates_runtime_modules(self) -> None:
        user_code = (
            "import mcp\n"
            "import mcp.servers.demo_server as demo\n"
            "result = await demo.list_things()\n"
            "assert result == ['ok']\n"
            "assert 'demo-server' in mcp_servers\n"
            "assert 'demo_server' in mcp.servers.__all__\n"
        )

        result = _run_entrypoint(user_code)

        self.assertTrue(
            any(call.get("type") == "rpc_request" for call in result["calls"])
        )
        self.assertEqual(result["stdout"], "")
        self.assertEqual(result["stderr"], "")
        self.assertIsInstance(result["sandbox_exports"], dict)
        sandbox_exports = result["sandbox_exports"]
        self.assertIsNotNone(sandbox_exports)
        if sandbox_exports is not None:
            self.assertIn("demo-server", sandbox_exports)
        demo_module = result["demo_module"]
        self.assertIsNotNone(demo_module)
        if demo_module is not None:
            self.assertTrue(hasattr(demo_module, "list_things"))
        runtime_module = result["runtime_module"]
        mcp_package = result["mcp_package"]
        self.assertIsNotNone(runtime_module)
        self.assertIsNotNone(mcp_package)
        if runtime_module is not None:
            self.assertEqual(runtime_module.discovered_servers(), ("demo-server",))
            self.assertTrue(hasattr(runtime_module, "query_tool_docs"))
            self.assertTrue(hasattr(runtime_module, "search_tool_docs"))
        if runtime_module is not None and mcp_package is not None:
            self.assertIs(getattr(mcp_package, "runtime", None), runtime_module)

    def test_runtime_helpers_sync_and_async_behaviour(self) -> None:
        user_code = (
            "from mcp import runtime\n"
            "assert runtime.list_servers_sync() == ('demo-server',)\n"
            "docs_sync = runtime.query_tool_docs_sync('demo-server')\n"
            "assert docs_sync and docs_sync[0]['toolAlias'] == 'list_things'\n"
            "search_sync = runtime.search_tool_docs_sync('list')\n"
            "assert search_sync and search_sync[0]['toolAlias'] == 'list_things'\n"
            "summary = runtime.capability_summary()\n"
            "print('SUMMARY:', summary)\n"
            "async def _exercise_async():\n"
            "    docs = await runtime.query_tool_docs('demo-server')\n"
            "    search = await runtime.search_tool_docs('list')\n"
            "    servers = await runtime.list_servers()\n"
            "    print('ASYNC:', docs, search, servers)\n"
            "await _exercise_async()\n"
        )

        result = _run_entrypoint(user_code)

        self.assertEqual(result["stderr"], "")
        self.assertIn("SUMMARY:", result["stdout"])

        runtime_module = result["runtime_module"]
        self.assertIsNotNone(runtime_module)
        if runtime_module is not None:
            list_servers_sync = getattr(runtime_module, "list_servers_sync", None)
            self.assertIsNotNone(list_servers_sync)
            if list_servers_sync is not None:
                self.assertEqual(list_servers_sync(), ("demo-server",))
            list_tools_sync = getattr(runtime_module, "list_tools_sync", None)
            self.assertIsNotNone(list_tools_sync)
            if list_tools_sync is not None:
                tool_aliases = [
                    tool["alias"] for tool in list_tools_sync("demo-server")
                ]
                self.assertEqual(tool_aliases, ["list_things"])
            query_sync = getattr(runtime_module, "query_tool_docs_sync", None)
            self.assertIsNotNone(query_sync)
            docs_sync = query_sync("demo-server") if query_sync is not None else []
            self.assertEqual(docs_sync[0]["toolAlias"], "list_things")
            search_sync_fn = getattr(runtime_module, "search_tool_docs_sync", None)
            self.assertIsNotNone(search_sync_fn)
            search_sync = search_sync_fn("list") if search_sync_fn is not None else []
            self.assertEqual(search_sync[0]["toolAlias"], "list_things")
            summary_fn = getattr(runtime_module, "capability_summary", None)
            self.assertIsNotNone(summary_fn)
            if summary_fn is not None:
                self.assertIn("PYTHON SANDBOX MANUAL", summary_fn())

        rpc_types = [payload.get("type") for payload in result["rpc_payloads"]]
        self.assertIn("query_tool_docs", rpc_types)
        self.assertIn("search_tool_docs", rpc_types)
        self.assertIn("list_servers", rpc_types)

    def test_runtime_metadata_helpers_and_errors(self) -> None:
        user_code = (
            "from mcp import runtime\n"
            "assert runtime.discovered_servers() == ('demo-server',)\n"
            "meta = runtime.list_loaded_server_metadata()\n"
            "assert isinstance(meta, tuple) and meta and meta[0]['alias'] == 'demo_server'\n"
            "desc = runtime.describe_server('demo-server')\n"
            "assert desc['name'] == 'demo-server'\n"
            "try:\n"
            "    runtime.list_tools_sync()\n"
            "except runtime.MCPError:\n"
            "    print('EXPECTED_SYNC_ERROR')\n"
            "else:\n"
            "    raise AssertionError('list_tools_sync should require a server name')\n"
            "doc_full = await runtime.query_tool_docs('demo-server', tool='list_things', detail='full')\n"
            "assert isinstance(doc_full, dict) and 'inputSchema' in doc_full\n"
            "search_full = await runtime.search_tool_docs('list', limit=1, detail='full')\n"
            "assert search_full and len(search_full) == 1 and 'inputSchema' in search_full[0]\n"
            "sync_results = runtime.search_tool_docs_sync('list demo', limit=1, detail='full')\n"
            "assert sync_results and 'inputSchema' in sync_results[0]\n"
        )

        result = _run_entrypoint(user_code)

        self.assertEqual(result["stderr"], "")
        self.assertIn("EXPECTED_SYNC_ERROR", result["stdout"])

        runtime_module = result["runtime_module"]
        self.assertIsNotNone(runtime_module)
        if runtime_module is not None:
            metadata_tuple = runtime_module.list_loaded_server_metadata()
            self.assertEqual(metadata_tuple[0]["alias"], "demo_server")
            # The server metadata includes optional 'cwd' if configured
            self.assertEqual(metadata_tuple[0].get("cwd"), "/home/demo/projects")
            described = runtime_module.describe_server("demo-server")
            self.assertEqual(described["name"], "demo-server")
            self.assertEqual(described.get("cwd"), "/home/demo/projects")

        def test_runtime_describe_includes_cwd(self) -> None:
            user_code = (
                "from mcp import runtime\n"
                "desc = runtime.describe_server('demo-server')\n"
                "print('CWD:', desc.get('cwd'))\n"
            )
            result = _run_entrypoint(user_code)
            self.assertEqual(result["stderr"], "")
            self.assertIn("CWD:", result["stdout"])

        query_full_payloads = [
            payload
            for payload in result["rpc_payloads"]
            if payload.get("type") == "query_tool_docs"
            and payload.get("detail") == "full"
        ]
        self.assertTrue(query_full_payloads)
        self.assertEqual(query_full_payloads[0].get("tool"), "list_things")

        search_full_payloads = [
            payload
            for payload in result["rpc_payloads"]
            if payload.get("type") == "search_tool_docs"
            and payload.get("detail") == "full"
        ]
        self.assertTrue(search_full_payloads)
        self.assertTrue(
            all(payload.get("limit") == 1 for payload in search_full_payloads)
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
