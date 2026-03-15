"""
Offline tests for Brave Search LangChain tool (no network calls).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.modules.tools.osint import bravesearch_langchain as mod
from shared.modules.tools.osint.bravesearch_langchain import bravesearch_domain_search


def _dummy_runtime(api_key: str | None = "k"):
    env = {"BRAVE_API_KEY": api_key} if api_key else {}
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


def test_brave_missing_key():
    runtime = _dummy_runtime(api_key=None)
    r = _call_tool(bravesearch_domain_search, runtime=runtime, word="example.com", limit=20)
    d = json.loads(r)
    assert d["status"] == "error"
    assert d["error_type"] == "missing_key"


def test_brave_success_offline_extracts():
    runtime = _dummy_runtime(api_key="abc123")

    orig_get = mod._SESSION.get

    def fake_get(url, headers=None, timeout=None):
        # Return a single page with two results containing an email + hostnames
        return _FakeResp(
            {
                "web": {
                    "results": [
                        {
                            "title": "Contact",
                            "description": "security@example.com",
                            "extra_snippets": ["admin@sub2.example.com"],
                            "url": "https://sub1.example.com/page",
                        },
                        {"title": "Login", "description": "", "url": "https://sub2.example.com/login"},
                    ]
                }
            },
            200,
        )

    mod._SESSION.get = fake_get
    try:
        r = _call_tool(bravesearch_domain_search, runtime=runtime, word="example.com", limit=20)
        d = json.loads(r)
        assert d["status"] == "success", d
        assert "security@example.com" in d.get("emails", []), d
        assert "admin@sub2.example.com" in d.get("emails", []), d
        hosts = set(d.get("hostnames", []))
        assert "sub1.example.com" in hosts, hosts
        assert "sub2.example.com" in hosts, hosts
    finally:
        mod._SESSION.get = orig_get


