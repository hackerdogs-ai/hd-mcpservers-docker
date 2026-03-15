"""
Offline functional-ish tests for theHarvester-style Baidu search LangChain tool.

No network calls:
- We monkeypatch the module-level requests Session `.get` to return deterministic HTML.
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

from shared.modules.tools.osint import baidusearch_langchain as mod
from shared.modules.tools.osint.baidusearch_langchain import baidu_search_web


def _dummy_runtime():
    return SimpleNamespace(state={"user_id": "test_user", "environment_variables": {}, "api_keys": {}})


def _call_tool(tool_obj, **kwargs) -> str:
    fn = getattr(tool_obj, "func", None)
    if callable(fn):
        return fn(**kwargs)
    inv = getattr(tool_obj, "invoke", None)
    if callable(inv):
        return inv(kwargs)
    raise TypeError(f"Unsupported tool object type: {type(tool_obj).__name__}")


class _FakeResp:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code


def test_baidu_search_web_offline_extracts_emails_and_hostnames():
    runtime = _dummy_runtime()

    html1 = """
    <html>
      <body>
        Contact: security@example.com
        <a href="https://sub1.example.com/page">r1</a>
      </body>
    </html>
    """
    html2 = """
    <html>
      <body>
        Email: admin@sub2.example.com
        <a href="https://sub2.example.com/login">r2</a>
      </body>
    </html>
    """

    calls = {"n": 0}
    orig_get = mod._SESSION.get

    def fake_get(url, headers=None, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return _FakeResp(html1, 200)
        return _FakeResp(html2, 200)

    mod._SESSION.get = fake_get
    try:
        r = _call_tool(baidu_search_web, runtime=runtime, word="example.com", limit=20)
        d = json.loads(r)
        assert d.get("status") == "success", d
        emails = set(d.get("emails", []))
        assert "security@example.com" in emails, emails
        assert "admin@sub2.example.com" in emails, emails

        hostnames = set(d.get("hostnames", []))
        assert "sub1.example.com" in hostnames, hostnames
        assert "sub2.example.com" in hostnames, hostnames
        assert d.get("fetched_urls", 0) >= 1, d
    finally:
        mod._SESSION.get = orig_get


def test_baidu_search_web_validation():
    runtime = _dummy_runtime()
    r = _call_tool(baidu_search_web, runtime=runtime, word="  ", limit=50)
    d = json.loads(r)
    assert d.get("status") == "error", d
    assert d.get("error_type") == "validation_error", d


def main() -> int:
    test_baidu_search_web_validation()
    test_baidu_search_web_offline_extracts_emails_and_hostnames()
    print("OK: baidu_search_web (theHarvester-style) offline tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


