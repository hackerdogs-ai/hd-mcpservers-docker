"""
Functional smoke tests for SpiderFoot-migrated LangChain tools:
- AdGuard DNS
- Ahmia
- Apple iTunes
- Archive.org Wayback
- ARIN

These are network tests (best-effort). They verify:
- tools return JSON
- status is ok
- expected top-level keys exist

Run in an environment where deps are installed and outbound network is allowed.
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

from shared.modules.tools.osint.adguard_dns_langchain import adguard_dns_check_host
from shared.modules.tools.osint.ahmia_langchain import ahmia_search
from shared.modules.tools.osint.apple_itunes_langchain import apple_itunes_search_apps_for_domain
from shared.modules.tools.osint.archiveorg_langchain import wayback_available
from shared.modules.tools.osint.arin_langchain import arin_lookup


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


def _assert_ok(resp_json: str) -> dict:
    data = json.loads(resp_json)
    assert data.get("status") == "ok", data
    return data


def test_adguard_dns():
    runtime = _dummy_runtime()
    data = _assert_ok(_call_tool(adguard_dns_check_host, runtime=runtime, host="example.com", mode="both"))
    assert "blocked_default" in data and "blocked_family" in data


def test_ahmia():
    runtime = _dummy_runtime()
    data = _assert_ok(_call_tool(ahmia_search, runtime=runtime, query="test", max_results=5, only_onion=False, fetch_content=False))
    assert "results" in data and "result_count" in data


def test_itunes():
    runtime = _dummy_runtime()
    data = _assert_ok(_call_tool(apple_itunes_search_apps_for_domain, runtime=runtime, domain="google.com", limit=25))
    assert "matches" in data and "match_count" in data


def test_wayback():
    runtime = _dummy_runtime()
    data = _assert_ok(_call_tool(wayback_available, runtime=runtime, url="https://example.com", days_back_csv="30"))
    assert "snapshots" in data


def test_arin():
    runtime = _dummy_runtime()
    data = _assert_ok(_call_tool(arin_lookup, runtime=runtime, query_type="domain", value="arin.net", resolve_contacts=False))
    assert "result" in data


def main() -> int:
    test_adguard_dns()
    test_ahmia()
    test_itunes()
    test_wayback()
    test_arin()
    print("OK: SpiderFoot-migrated LangChain tool smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



