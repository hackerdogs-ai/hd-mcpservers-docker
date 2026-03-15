"""
Tests for Masscan LangChain tool.

Validates:
1. An LLM can call the tool (import, invoke with runtime, get JSON response).
2. The tool is reachable via the same loading path as chat (module + function name).
3. Docstrings are present and describe the tool for LLM consumption.

Run from repo root with project deps installed, e.g.:
  python shared/modules/tools/tests/test_masscan_langchain_tools.py
  pytest shared/modules/tools/tests/test_masscan_langchain_tools.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

# Repo root on path for shared.* imports when run as script
# __file__ = .../shared/modules/tools/tests/test_masscan_langchain_tools.py -> parents[4] = repo root
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Tool module/function as registered in g_tools (insert_osint_tools_infra.sql)
TOOL_MODULE_NAME = "shared.modules.tools.osint.masscan_langchain"
TOOL_FUNCTION_NAME = "masscan_scan"


def _call_tool(tool_obj, **kwargs) -> str:
    """Invoke a LangChain @tool (has .func or .invoke)."""
    fn = getattr(tool_obj, "func", None)
    if callable(fn):
        return fn(**kwargs)
    inv = getattr(tool_obj, "invoke", None)
    if callable(inv):
        return inv(kwargs)
    raise TypeError(f"Unsupported tool object type: {type(tool_obj).__name__}")


def _assert_json(resp: str) -> dict:
    data = json.loads(resp)
    assert isinstance(data, dict), "Response must be a JSON object"
    assert data.get("status") in ("success", "error"), f"Unexpected status: {data.get('status')}"
    return data


def test_llm_can_call_tool():
    """1. Can an LLM call it? Import and invoke with minimal args; expect JSON (error ok if no Docker)."""
    from shared.modules.tools.osint.masscan_langchain import masscan_scan

    runtime = SimpleNamespace(state={"user_id": "test_user", "environment_variables": {}, "api_keys": {}})
    out = _call_tool(masscan_scan, runtime=runtime, ip_range="192.168.1.0/24", ports="80", rate=1000)
    d = _assert_json(out)
    # With Docker: success with open_ports. Without Docker: error about Docker required.
    assert "status" in d
    if d["status"] == "success":
        assert "open_ports" in d
        assert "summary" in d
    else:
        assert "message" in d


def test_validation_rejects_bad_inputs():
    """Tool returns JSON error for invalid ip_range and ports."""
    from shared.modules.tools.osint.masscan_langchain import masscan_scan

    runtime = SimpleNamespace(state={"user_id": "test_user", "environment_variables": {}, "api_keys": {}})
    r = _call_tool(masscan_scan, runtime=runtime, ip_range="", ports="80", rate=1000)
    d = _assert_json(r)
    assert d["status"] == "error"
    assert "ip_range" in (d.get("message") or "").lower() or "non-empty" in (d.get("message") or "").lower()

    r2 = _call_tool(masscan_scan, runtime=runtime, ip_range="10.0.0.1", ports="", rate=1000)
    d2 = _assert_json(r2)
    assert d2["status"] == "error"
    assert "ports" in (d2.get("message") or "").lower() or "non-empty" in (d2.get("message") or "").lower()


def test_tool_reachable_by_module_and_function_name():
    """2. Is the tool reachable? Load the same way chat_streaming_tasks does (module + function name)."""
    module = __import__(TOOL_MODULE_NAME, fromlist=[TOOL_FUNCTION_NAME])
    tool_function = getattr(module, TOOL_FUNCTION_NAME, None)
    assert tool_function is not None, (
        f"Tool function '{TOOL_FUNCTION_NAME}' not found in module '{TOOL_MODULE_NAME}'"
    )
    assert callable(tool_function), f"'{TOOL_FUNCTION_NAME}' is not callable"


def test_docstring_present_and_describes_tool():
    """3. Are docstrings properly written for the tool (LLM and docs)?"""
    from shared.modules.tools.osint.masscan_langchain import masscan_scan

    doc = masscan_scan.description if hasattr(masscan_scan, "description") else getattr(masscan_scan, "__doc__", "") or ""
    assert doc, "Tool should have a description or __doc__ for LLM"
    doc_lower = doc.lower()
    assert "masscan" in doc_lower, "Docstring should mention masscan"
    assert "port" in doc_lower, "Docstring should mention port(s)"
    assert "ip_range" in doc_lower or "ip" in doc_lower, "Docstring should mention ip_range or IP"
    assert "json" in doc_lower or "open_ports" in doc_lower or "returns" in doc_lower, (
        "Docstring should describe return value (JSON / open_ports / Returns)"
    )


def main() -> int:
    try:
        from shared.modules.tools.osint.masscan_langchain import masscan_scan  # noqa: F401
    except ImportError as e:
        print(f"SKIP: Project dependencies not installed ({e}). Install e.g. pip install -r requirements.txt")
        return 0
    test_validation_rejects_bad_inputs()
    test_docstring_present_and_describes_tool()
    test_tool_reachable_by_module_and_function_name()
    test_llm_can_call_tool()
    print("OK: Masscan LangChain tool validated (LLM-callable, reachable, docstrings).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
