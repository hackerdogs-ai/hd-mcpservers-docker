"""
Executable validation script for OWASP ZAP LangChain tool.

This follows the repo style of lightweight "tool wiring" validation scripts.

It validates:
- Basic parameter validation (bad target URL)
- Docker-not-available error handling (most CI/dev envs without Docker)
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

from shared.modules.tools.osint.owazp_zap_langchain import owasp_zap_scan


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


def test_validation_bad_url():
    runtime = SimpleNamespace(state={"user_id": "test_user", "environment_variables": {}, "api_keys": {}})
    r = _call_tool(owasp_zap_scan, runtime=runtime, target="not-a-url")
    d = _assert_json(r)
    assert d["status"] == "error"
    assert "http" in (d.get("message") or "").lower()


def test_docker_unavailable_returns_error():
    runtime = SimpleNamespace(state={"user_id": "test_user", "environment_variables": {}, "api_keys": {}})
    # Use dry_run to avoid any actual scanning/network activity.
    r = _call_tool(owasp_zap_scan, runtime=runtime, target="https://example.com", scan_level="baseline", dry_run=True)
    d = _assert_json(r)
    assert d["status"] == "success"
    assert d.get("dry_run") is True
    docker = d.get("docker") or {}
    assert isinstance(docker, dict)
    assert docker.get("image")
    assert isinstance(docker.get("args"), list) and len(docker.get("args")) > 0
    assert isinstance(docker.get("volumes"), list) and len(docker.get("volumes")) > 0


def main() -> int:
    test_validation_bad_url()
    test_docker_unavailable_returns_error()
    print("OK: OWASP ZAP LangChain tool validated (validation + docker error handling).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


