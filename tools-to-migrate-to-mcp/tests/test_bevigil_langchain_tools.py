"""
Offline tests for BeVigil LangChain tool.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

# Ensure repo root is importable so `shared.*` imports work when running under pytest
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.modules.tools.osint import bevigil_langchain as mod
from shared.modules.tools.osint.bevigil_langchain import bevigil_domain_osint


def _dummy_runtime(api_key: str | None = "k"):
    env = {"BEVIGIL_API_KEY": api_key} if api_key else {}
    return SimpleNamespace(state={"user_id": "test_user", "environment_variables": {"default": env}, "api_keys": {}})


def _call_tool(tool_obj, **kwargs) -> str:
    fn = getattr(tool_obj, "func", None)
    if callable(fn):
        return fn(**kwargs)
    inv = getattr(tool_obj, "invoke", None)
    if callable(inv):
        return inv(kwargs)
    raise TypeError(f"Unsupported tool object type: {type(tool_obj).__name__}")


class _FakeResp:
    def __init__(self, json_obj, status_code: int = 200):
        self._json = json_obj
        self.status_code = status_code
        self.text = json.dumps(json_obj)

    def json(self):
        return self._json


def test_bevigil_missing_key():
    runtime = _dummy_runtime(api_key=None)
    r = _call_tool(bevigil_domain_osint, runtime=runtime, domain="example.com")
    d = json.loads(r)
    assert d["status"] == "error"
    assert d["error_type"] == "missing_key"


def test_bevigil_success_offline():
    runtime = _dummy_runtime(api_key="abc123")

    orig_get = mod._SESSION.get
    calls = {"n": 0}

    def fake_get(url, headers=None, timeout=None):
        calls["n"] += 1
        if url.endswith("/subdomains/"):
            return _FakeResp({"subdomains": ["a.example.com", "b.example.com"]}, 200)
        if url.endswith("/urls/"):
            return _FakeResp({"urls": ["https://a.example.com/", "https://b.example.com/login"]}, 200)
        return _FakeResp({"error": "unexpected"}, 404)

    mod._SESSION.get = fake_get
    try:
        r = _call_tool(bevigil_domain_osint, runtime=runtime, domain="example.com")
        d = json.loads(r)
        assert d["status"] == "success", d
        assert set(d["hostnames"]) == {"a.example.com", "b.example.com"}
        assert any(u.endswith("/login") for u in d["interesting_urls"])
    finally:
        mod._SESSION.get = orig_get


