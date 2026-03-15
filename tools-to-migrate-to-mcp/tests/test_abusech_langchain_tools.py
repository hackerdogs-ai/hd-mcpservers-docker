"""
Executable validation script for AbuseCH LangChain tools.

This is implemented as an executable script (not pytest-only), matching the style
of other tool validation scripts in this repo.

It validates:
- ToolRuntime key retrieval via runtime.state["environment_variables"]
- Basic call path wiring (tool invocation and JSON response shape)

Note:
- If you provide a real AbuseCH API key via environment variable ABUSECH_API_KEY,
  this script will perform a live request. Otherwise it will only validate
  "missing key" error handling.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

# Ensure repo root is importable so `shared.*` imports work when running as a script
# This file lives at: <repo>/shared/modules/tools/tests/<this_file>
# parents[0]=tests, [1]=tools, [2]=modules, [3]=shared, [4]=<repo>
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.modules.tools.osint.abusech_langchain import (
    abusech_ip_report,
    abusech_domain_report,
    abusech_url_report,
    abusech_file_report,
)


def _runtime_with_key(key: str | None):
    env_vars = {}
    if key:
        env_vars = {"abusech_instance": {"ABUSECH_API_KEY": key}}
    return SimpleNamespace(state={"user_id": "test_user", "environment_variables": env_vars, "api_keys": {}})


def _call_tool(tool_obj, **kwargs) -> str:
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


def test_missing_key_errors():
    runtime = _runtime_with_key(None)
    r = _call_tool(abusech_ip_report, runtime=runtime, ip="8.8.8.8")
    d = _assert_json(r)
    assert d["status"] == "error"
    assert "ABUSECH_API_KEY" in (d.get("message") or "")


def test_live_request_if_key_present():
    key = os.environ.get("ABUSECH_API_KEY")
    if not key:
        return

    runtime = _runtime_with_key(key)

    # Use a stable, commonly present domain; URLhaus may still return "no_results"
    r1 = _call_tool(abusech_domain_report, runtime=runtime, domain="example.com")
    d1 = _assert_json(r1)
    assert "raw_response" in d1

    # Small smoke tests (do not assert success, since intelligence may be empty)
    r2 = _call_tool(abusech_url_report, runtime=runtime, url="http://example.com")
    d2 = _assert_json(r2)
    assert "raw_response" in d2

    # Avoid file hash live calls by default (can be rate-limited); uncomment if needed.
    # r3 = _call_tool(abusech_file_report, runtime=runtime, hash_value="44d88612fea8a8f36de82e1278abb02f")
    # d3 = _assert_json(r3)
    # assert "raw_response" in d3


def main() -> int:
    test_missing_key_errors()
    test_live_request_if_key_present()
    print("OK: AbuseCH LangChain tools validated (runtime key injection + basic call path).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



