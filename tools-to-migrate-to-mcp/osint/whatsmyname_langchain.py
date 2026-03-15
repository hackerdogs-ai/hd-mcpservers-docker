"""
WhatsMyName Tool for LangChain Agents

WhatsMyName is a community-maintained OSINT dataset + checking logic for finding
username presence across many websites.

Reference:
- Project: https://github.com/WebBreacher/WhatsMyName
- Dataset: https://raw.githubusercontent.com/WebBreacher/WhatsMyName/main/wmn-data.json

This module provides a LangChain tool wrapper around the WhatsMyName dataset,
following Hackerdogs OSINT tool standards:
- ToolRuntime-aware configuration (optional defaults)
- safe_log_* structured logging
- defensive input validation and exception handling
- JSON output returned to the agent

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

These are optional and can be supplied via ToolRuntime. Resolution order:
1) runtime.state["environment_variables"][<instance>][KEY]  (preferred)
2) runtime.state["environment_variables"][KEY]              (flat dict fallback)
3) runtime.state["api_keys"][KEY]                           (fallback used by other tools)

Supported keys:
- WMN_DATA_URL: URL to fetch wmn-data.json (default: official GitHub raw URL)
- WMN_REQUEST_TIMEOUT: Per-site HTTP timeout (seconds, default: 10)
- WMN_MAX_WORKERS: Max concurrent site checks (default: 20)
- WMN_USER_AGENT: User-Agent for HTTP requests (default: modern Chrome UA)

Security Notes:
- Usernames are logged for audit purposes (not sensitive, but logged).
- This tool makes outbound HTTP GET requests to third-party sites; treat results
  as best-effort and subject to false positives/negatives.
- HTML report generation is optional and writes a local file (disabled by default).
"""

from __future__ import annotations

import html
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from langchain.tools import ToolRuntime, tool
from hd_logging import setup_logger

from shared.modules.tools.tool_logging import safe_log_debug, safe_log_error, safe_log_info

logger = setup_logger(__name__, log_file_path="logs/whatsmyname_tool.log")

# Reuse connections under load
_SESSION = requests.Session()

_DEFAULT_WMN_DATA_URL = "https://raw.githubusercontent.com/WebBreacher/WhatsMyName/main/wmn-data.json"
_DEFAULT_TIMEOUT_SECONDS = 10
_DEFAULT_MAX_WORKERS = 20
_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _get_runtime_env(runtime: ToolRuntime, key: str) -> Optional[str]:
    """
    Get an environment variable from ToolRuntime state.

    Resolution order:
    1) runtime.state["environment_variables"][<instance>][key]
    2) runtime.state["environment_variables"][key] (flat dict fallback)
    3) runtime.state["api_keys"][key] (fallback used by other tools)
    """
    try:
        if not runtime or not getattr(runtime, "state", None):
            return None

        env_vars = runtime.state.get("environment_variables", {})
        if isinstance(env_vars, dict):
            # Preferred: instance-scoped mapping
            for instance_name, instance_env in env_vars.items():
                if isinstance(instance_env, dict) and key in instance_env and instance_env.get(key):
                    safe_log_debug(
                        logger,
                        "[whatsmyname] Found runtime env var",
                        key=key,
                        instance_name=instance_name,
                    )
                    return str(instance_env.get(key))

            # Fallback: flat dict
            if key in env_vars and env_vars.get(key):
                safe_log_debug(logger, "[whatsmyname] Found runtime env var (flat)", key=key)
                return str(env_vars.get(key))

        api_keys = runtime.state.get("api_keys", {})
        if isinstance(api_keys, dict) and key in api_keys and api_keys.get(key):
            safe_log_debug(logger, "[whatsmyname] Found runtime api key", key=key)
            return str(api_keys.get(key))
    except Exception:
        return None

    return None


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _sanitize_username(username: str) -> str:
    """
    Normalize username input.

    WhatsMyName dataset typically expects simple usernames. We allow a broad set,
    but strip whitespace and reject obviously unsafe/empty values.
    """
    if not isinstance(username, str):
        return ""
    return username.strip()


def _default_headers(runtime: ToolRuntime) -> Dict[str, str]:
    """
    Build default HTTP headers for site checks.

    Caller/tool can override WMN_USER_AGENT via ToolRuntime.
    """
    ua = _get_runtime_env(runtime, "WMN_USER_AGENT") or _DEFAULT_USER_AGENT
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "User-Agent": ua,
    }


def _fetch_wmn_dataset(*, data_url: str, timeout: int) -> Tuple[bool, str, Optional[dict]]:
    """
    Fetch and parse WhatsMyName dataset.

    Returns:
        (ok, message, data)
    """
    try:
        resp = _SESSION.get(data_url, timeout=timeout)
        safe_log_debug(
            logger,
            "[whatsmyname] Dataset fetch response",
            status_code=resp.status_code,
            content_length=len(resp.content) if resp.content else 0,
        )
        if resp.status_code >= 400:
            return False, f"Failed to fetch dataset: HTTP {resp.status_code}", None
        try:
            data = resp.json()
        except Exception:
            return False, "Failed to parse dataset as JSON", None

        if not isinstance(data, dict) or "sites" not in data or not isinstance(data.get("sites"), list):
            return False, "Dataset JSON missing required 'sites' list", None

        return True, "ok", data
    except requests.exceptions.Timeout as e:
        return False, f"Dataset fetch timeout: {str(e)}", None
    except requests.exceptions.RequestException as e:
        return False, f"Dataset fetch request error: {str(e)}", None
    except Exception as e:
        return False, f"Dataset fetch unexpected error: {str(e)}", None


@dataclass(frozen=True)
class _CheckResult:
    site_name: str
    profile_url: str


def _site_required_fields_present(site: Dict[str, Any]) -> bool:
    required = ["name", "uri_check", "e_code", "e_string", "m_string"]
    for k in required:
        if k not in site:
            return False
    return True


def _check_site(
    *,
    site: Dict[str, Any],
    username: str,
    headers: Dict[str, str],
    timeout: int,
) -> Optional[_CheckResult]:
    """
    Check a single site for a username.

    WhatsMyName matching logic:
    - Request uri_check with username substituted
    - "exists" if:
      - status_code == e_code
      - e_string is present in response body
      - m_string is NOT present in response body
    """
    try:
        if not _site_required_fields_present(site):
            return None

        site_name = str(site.get("name", "")).strip()
        uri_tmpl = site.get("uri_check")
        if not site_name or not isinstance(uri_tmpl, str) or "{account}" not in uri_tmpl:
            return None

        profile_url = uri_tmpl.format(account=username)
        resp = _SESSION.get(profile_url, headers=headers, timeout=timeout, allow_redirects=True)

        # Defensive: some sites return binary/odd encodings; requests.text best-effort decodes.
        body = resp.text or ""

        expected_code = site.get("e_code")
        pos = site.get("e_string") or ""
        neg = site.get("m_string") or ""

        # Coerce expected_code to int if possible
        try:
            expected_code_i = int(expected_code)
        except Exception:
            return None

        estring_pos = bool(pos) and (str(pos) in body)
        estring_neg = bool(neg) and (str(neg) in body)

        if resp.status_code == expected_code_i and estring_pos and not estring_neg:
            return _CheckResult(site_name=site_name, profile_url=profile_url)
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.RequestException:
        return None
    except Exception:
        return None

    return None


def _generate_html_report(*, username: str, found: List[_CheckResult], output_dir: Path) -> Path:
    """
    Generate an HTML report file for found results.

    This is optional and should only be called when explicitly requested.
    """
    safe_username = re.sub(r"[^a-zA-Z0-9._-]+", "_", username)[:120] or "username"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"whatsmyname_report_{safe_username}.html"

    rows = []
    for r in found:
        site_name = html.escape(r.site_name)
        url = html.escape(r.profile_url)
        rows.append(f"<tr><td>{site_name}</td><td><a href=\"{url}\" target=\"_blank\">{url}</a></td></tr>")

    content = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>WhatsMyName Report for {html.escape(username)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background-color: #f2f2f2; }}
  </style>
</head>
<body>
  <h1>WhatsMyName Report for {html.escape(username)}</h1>
  <p>Matches: {len(found)}</p>
  <table>
    <tr><th>Website Name</th><th>Profile URL</th></tr>
    {''.join(rows)}
  </table>
</body>
</html>
"""

    out_path.write_text(content, encoding="utf-8")
    return out_path


@tool
def whatsmyname_scan(
    runtime: ToolRuntime,
    username: str,
    sites: Optional[List[str]] = None,
    timeout: Optional[int] = None,
    max_workers: Optional[int] = None,
    limit: Optional[int] = 50,
    write_html_report: bool = False,
    report_output_dir: Optional[str] = None,
    dry_run: bool = False,
) -> str:
    """
    Scan WhatsMyName supported sites for a given username.

    Args:
        runtime: ToolRuntime instance (automatically injected).
        username: Target username to search (required).
        sites: Optional list of specific site names to check (default: all).
            Site names must match WhatsMyName dataset "name" field (case-insensitive).
        timeout: Per-site request timeout in seconds (default: WMN_REQUEST_TIMEOUT or 10).
            Range: 1-120.
        max_workers: Concurrency (default: WMN_MAX_WORKERS or 20). Range: 1-100.
        limit: Max number of matches to return (default: 50). Range: 1-500.
        write_html_report: If True, writes an HTML report locally and returns its path.
            Default: False.
        report_output_dir: Optional directory for report output (default: cwd).
        dry_run: If True, returns the planned configuration without network calls.

    Returns:
        JSON string:
        - On success:
          {
            "status": "success",
            "username": "example",
            "matches": [{"site": "GitHub", "url": "https://github.com/example"}, ...],
            "matches_count": 2,
            "checked_sites": 347,
            "skipped_sites": 0,
            "data_url": "...",
            "html_report_path": "..." (only if write_html_report=True and matches exist)
          }
        - On error:
          {"status": "error", "message": "..."}
    """
    try:
        safe_log_info(
            logger,
            "[whatsmyname_scan] Starting",
            username=username,
            sites=sites,
            timeout=timeout,
            max_workers=max_workers,
            limit=limit,
            write_html_report=write_html_report,
            dry_run=dry_run,
        )

        # Validate username
        username_norm = _sanitize_username(username)
        if not username_norm:
            return json.dumps({"status": "error", "message": "username must be a non-empty string"})

        # Resolve defaults from ToolRuntime
        data_url = (_get_runtime_env(runtime, "WMN_DATA_URL") or _DEFAULT_WMN_DATA_URL).strip()
        effective_timeout = int(timeout) if timeout is not None else _coerce_int(_get_runtime_env(runtime, "WMN_REQUEST_TIMEOUT"), _DEFAULT_TIMEOUT_SECONDS)
        effective_workers = int(max_workers) if max_workers is not None else _coerce_int(_get_runtime_env(runtime, "WMN_MAX_WORKERS"), _DEFAULT_MAX_WORKERS)

        # Handle string "None" from LLM (LangChain sometimes stringifies None)
        if report_output_dir in ("None", "none"):
            report_output_dir = None

        # Validate numeric parameters
        if not (1 <= effective_timeout <= 120):
            return json.dumps({"status": "error", "message": "timeout must be between 1 and 120 seconds"})
        if not (1 <= effective_workers <= 100):
            return json.dumps({"status": "error", "message": "max_workers must be between 1 and 100"})
        if limit is not None and not (1 <= int(limit) <= 500):
            return json.dumps({"status": "error", "message": "limit must be between 1 and 500"})

        # Dry run for validation/testing without network calls
        if dry_run:
            return json.dumps(
                {
                    "status": "success",
                    "dry_run": True,
                    "username": username_norm,
                    "data_url": data_url,
                    "timeout": effective_timeout,
                    "max_workers": effective_workers,
                    "sites": sites,
                    "limit": int(limit) if limit is not None else None,
                    "write_html_report": write_html_report,
                    "report_output_dir": report_output_dir,
                },
                indent=2,
            )

        # Fetch dataset
        ok, msg, dataset = _fetch_wmn_dataset(data_url=data_url, timeout=max(5, min(60, effective_timeout)))
        if not ok or not dataset:
            safe_log_error(logger, "[whatsmyname_scan] Dataset fetch failed", exc_info=False, message=msg, data_url=data_url)
            return json.dumps({"status": "error", "message": msg})

        all_sites = dataset.get("sites", [])
        if not isinstance(all_sites, list) or len(all_sites) == 0:
            return json.dumps({"status": "error", "message": "Dataset contains no sites"})

        # Optional site filtering (case-insensitive exact match on site["name"])
        filtered_sites = all_sites
        if sites:
            if not isinstance(sites, list) or any((not isinstance(s, str) or not s.strip()) for s in sites):
                return json.dumps({"status": "error", "message": "sites must be a list of non-empty strings"})
            requested = {s.strip().lower() for s in sites if s and isinstance(s, str)}
            index: Dict[str, Dict[str, Any]] = {}
            for s in all_sites:
                try:
                    name = str(s.get("name", "")).strip()
                    if name:
                        index[name.lower()] = s
                except Exception:
                    continue
            missing = sorted([r for r in requested if r not in index])
            if missing:
                return json.dumps(
                    {
                        "status": "error",
                        "message": "Some requested site names were not found in WhatsMyName dataset",
                        "missing_sites": missing,
                    },
                    indent=2,
                )
            filtered_sites = [index[r] for r in requested]

        headers = _default_headers(runtime)

        # Execute checks concurrently
        found: List[_CheckResult] = []
        skipped = 0

        safe_log_info(
            logger,
            "[whatsmyname_scan] Scanning",
            username=username_norm,
            sites_total=len(filtered_sites),
            max_workers=effective_workers,
            timeout=effective_timeout,
        )

        with ThreadPoolExecutor(max_workers=effective_workers) as executor:
            futures = []
            for site in filtered_sites:
                if not isinstance(site, dict) or not _site_required_fields_present(site):
                    skipped += 1
                    continue
                futures.append(
                    executor.submit(
                        _check_site,
                        site=site,
                        username=username_norm,
                        headers=headers,
                        timeout=effective_timeout,
                    )
                )

            for fut in as_completed(futures):
                try:
                    r = fut.result()
                    if r:
                        found.append(r)
                except Exception:
                    # Never fail the whole scan because one site had an issue
                    continue

        # Sort stable + apply limit
        found_sorted = sorted(found, key=lambda x: (x.site_name.lower(), x.profile_url))
        if limit is not None:
            found_sorted = found_sorted[: int(limit)]

        matches = [{"site": r.site_name, "url": r.profile_url} for r in found_sorted]

        html_report_path = None
        if write_html_report and found_sorted:
            out_dir = Path(report_output_dir) if report_output_dir else Path(os.getcwd())
            try:
                report_path = _generate_html_report(username=username_norm, found=found_sorted, output_dir=out_dir)
                html_report_path = str(report_path)
            except Exception as e:
                # Do not fail the scan due to report generation
                safe_log_error(
                    logger,
                    "[whatsmyname_scan] Failed to write HTML report",
                    exc_info=True,
                    error=str(e),
                    report_output_dir=str(out_dir),
                )

        resp = {
            "status": "success",
            "username": username_norm,
            "matches": matches,
            "matches_count": len(matches),
            "checked_sites": len(filtered_sites) - skipped,
            "skipped_sites": skipped,
            "data_url": data_url,
        }
        if html_report_path:
            resp["html_report_path"] = html_report_path

        safe_log_info(
            logger,
            "[whatsmyname_scan] Complete",
            username=username_norm,
            matches_count=len(matches),
            checked_sites=resp["checked_sites"],
            skipped_sites=skipped,
            html_report_path=html_report_path,
        )

        return json.dumps(resp, indent=2)
    except Exception as e:
        safe_log_error(logger, "[whatsmyname_scan] Error", exc_info=True, error=str(e), username=username if "username" in locals() else None)
        return json.dumps({"status": "error", "message": f"WhatsMyName scan failed: {str(e)}"})


