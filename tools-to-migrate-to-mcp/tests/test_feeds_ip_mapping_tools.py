"""
No-network tests for feeds_client + feed LangChain modules.

We use local file:// fixtures and temporary feed config JSON files to validate:
- text CIDR list parsing for cloud ranges
- IP membership lookup
- name server IP parsing + lookup
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

# Ensure repo root is importable so `shared.*` imports work when running as a script
# This file lives at: <repo>/shared/modules/tools/tests/<this_file>
# parents[0]=tests, [1]=tools, [2]=modules, [3]=shared, [4]=<repo>
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.modules.tools.feeds.feeds_client import (
    list_nameserver_ips,
    lookup_ip_in_cloud_ranges,
    lookup_nameserver_ip,
    lookup_range_in_cloud_ranges,
)


def _dummy_runtime():
    return SimpleNamespace(state={"user_id": "test_user", "environment_variables": {}, "api_keys": {}})


def test_cloud_text_cidr_feed_lookup():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        cidr_txt = d / "cloudflare.txt"
        cidr_txt.write_text("1.1.1.0/24\n2606:4700::/32\n", encoding="utf-8")

        cfg = {
            "cloudflare_ip_ranges_v4": {
                "url": f"file://{cidr_txt}",
                "description": "test cloudflare",
                "file_type": "txt",
                "download_type": "txt",
            }
        }
        cfg_path = d / "cloud.json"
        cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

        matches = lookup_ip_in_cloud_ranges(feed_config_filename=str(cfg_path), ip="1.1.1.1", max_results=10)
        assert matches, "Expected at least one match for 1.1.1.1"
        assert matches[0]["cidr"] == "1.1.1.0/24"
        assert matches[0]["provider"] == "Cloudflare"

        overlaps = lookup_range_in_cloud_ranges(
            feed_config_filename=str(cfg_path),
            cidr="1.1.1.0/25",
            mode="contains",
            max_results=10,
        )
        assert overlaps, "Expected match for contained_by relationship"


def test_nameserver_text_feed_lookup():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        ns_txt = d / "ns.md"
        ns_txt.write_text(
            "# Public resolvers\n8.8.8.8 - Google Public DNS\n1.1.1.1 - Cloudflare DNS\n",
            encoding="utf-8",
        )
        cfg = {
            "my_nameservers": {
                "url": f"file://{ns_txt}",
                "description": "test name servers",
                "file_type": "md",
                "download_type": "md",
            }
        }
        cfg_path = d / "ns.json"
        cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

        matches = lookup_nameserver_ip(feed_config_filename=str(cfg_path), ip="8.8.8.8", max_results=10)
        assert matches and matches[0]["ip"] == "8.8.8.8"
        assert matches[0]["source_key"] == "my_nameservers"
        assert (matches[0].get("label") or "").lower().find("google") != -1

        ips = list_nameserver_ips(feed_config_filename=str(cfg_path), max_results=100)
        assert {x["ip"] for x in ips} == {"8.8.8.8", "1.1.1.1"}


def main() -> int:
    test_cloud_text_cidr_feed_lookup()
    test_nameserver_text_feed_lookup()
    print("OK: feeds_client offline parsing + IP/CIDR mapping validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


