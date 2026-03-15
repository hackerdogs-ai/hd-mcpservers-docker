"""
Executable validation script for WhatsMyName LangChain tool.

This follows the repo style of lightweight "tool wiring" validation scripts.

It validates:
- Basic parameter validation (missing/empty username)
- Dry-run execution path (no network calls)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

# Ensure repo root is importable so `shared.*` imports work when running as a script
# This file lives at: <repo>/shared/modules/tools/tests/<this_file>
# parents[0]=tests, [1]=tools, [2]=modules, [3]=shared, [4]=<repo>
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.modules.tools.osint.whatsmyname_langchain import whatsmyname_scan


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


def test_validation_missing_username():
    runtime = SimpleNamespace(state={"user_id": "test_user", "environment_variables": {}, "api_keys": {}})
    r = _call_tool(whatsmyname_scan, runtime=runtime, username="")
    d = _assert_json(r)
    assert d["status"] == "error"
    assert "username" in (d.get("message") or "").lower()


def test_dry_run_success():
    runtime = SimpleNamespace(state={"user_id": "test_user", "environment_variables": {}, "api_keys": {}})
    r = _call_tool(
        whatsmyname_scan,
        runtime=runtime,
        username="exampleuser",
        dry_run=True,
        timeout=10,
        max_workers=5,
        limit=10,
        write_html_report=False,
    )
    d = _assert_json(r)
    assert d["status"] == "success"
    assert d.get("dry_run") is True
    assert d.get("username") == "exampleuser"
    assert isinstance(d.get("data_url"), str) and d.get("data_url")


def main() -> int:
    test_validation_missing_username()
    test_dry_run_success()
    print("OK: WhatsMyName LangChain tool validated (validation + dry_run).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



