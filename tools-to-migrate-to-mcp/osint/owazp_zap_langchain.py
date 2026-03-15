"""
OWASP ZAP Tool for LangChain Agents

Runs OWASP Zed Attack Proxy (ZAP) packaged scans via the official Docker images,
and returns structured JSON suitable for LLM consumption.

Supported scan levels:
- baseline: quick spider + passive scanning (safe-ish / CI friendly)
- full: spider + active scan (intrusive; can impact target)
- api: API active scan based on OpenAPI / GraphQL definition

References:
- ZAP Docker User Guide: https://www.zaproxy.org/docs/docker/about/

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

1. Docker Environment (Required)
   - ZAP runs via its official Docker image.
   - Default image: zaproxy/zap-stable
   - Override with env var:
       ZAP_DOCKER_IMAGE="zaproxy/zap-stable"

2. Networking note (important)
   - If your target app is running on your host, the container cannot reach
     `localhost` / `127.0.0.1` directly. Use an address reachable from Docker
     (e.g., host.docker.internal on macOS, or a bridge IP as described in the
     ZAP Docker docs).

Security notes:
- Full scans are intrusive. Only scan targets you own / have explicit permission to test.
- Reports may include sensitive URLs/params; avoid logging full report bodies.
"""

from __future__ import annotations

import json
import os
import tempfile
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal, Tuple
from urllib.parse import urlparse

from langchain.tools import tool, ToolRuntime

from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug
from shared.modules.tools.docker_client import get_docker_client, execute_official_docker_image

logger = setup_logger(__name__, log_file_path="logs/owasp_zap_tool.log")

ZapScanLevel = Literal["baseline", "full", "api"]
ApiFormat = Literal["openapi", "graphql"]


def _check_docker_available() -> bool:
    client = get_docker_client()
    return client is not None and client.docker_available


def _is_http_url(value: str) -> bool:
    try:
        p = urlparse(value)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def _validate_target_url(target: str) -> Optional[str]:
    if not target or not isinstance(target, str) or len(target.strip()) == 0:
        return "target must be a non-empty string"
    target = target.strip()
    if not _is_http_url(target):
        return "target must be a valid http(s) URL (e.g., https://example.com)"
    return None


def _read_text_if_exists(path: Path, max_chars: int = 250_000) -> Optional[str]:
    try:
        if not path.exists():
            return None
        txt = path.read_text(errors="replace")
        if len(txt) > max_chars:
            return txt[:max_chars] + "\n...[TRUNCATED]..."
        return txt
    except Exception:
        return None


def _read_json_if_exists(path: Path) -> Optional[Any]:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(errors="replace"))
    except Exception:
        return None


def _summarize_zap_report(report_json: Any, max_alerts: int = 50) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
    """
    Best-effort extraction of alerts from ZAP JSON reports produced by packaged scripts.

    Expected shape (commonly):
    {
      "site": [
        {
          "@name": "...",
          "alerts": [
            { "name": "...", "riskdesc": "High (3)", "desc": "...", "solution": "...", "instances": [...] }
          ]
        }
      ]
    }
    """
    risk_counts: Dict[str, int] = {}
    alerts_out: List[Dict[str, Any]] = []

    if not isinstance(report_json, dict):
        return risk_counts, alerts_out

    sites = report_json.get("site")
    if isinstance(sites, dict):
        sites = [sites]
    if not isinstance(sites, list):
        return risk_counts, alerts_out

    for site in sites:
        if not isinstance(site, dict):
            continue
        alerts = site.get("alerts")
        if isinstance(alerts, dict):
            alerts = [alerts]
        if not isinstance(alerts, list):
            continue

        for a in alerts:
            if not isinstance(a, dict):
                continue
            riskdesc = str(a.get("riskdesc") or a.get("risk") or "Unknown").strip()
            # Normalize: "High (3)" -> "High"
            risk_label = riskdesc.split("(")[0].strip() if "(" in riskdesc else riskdesc
            risk_counts[risk_label] = risk_counts.get(risk_label, 0) + 1

            if len(alerts_out) < max_alerts:
                alerts_out.append(
                    {
                        "name": a.get("name"),
                        "risk": risk_label,
                        "riskdesc": a.get("riskdesc"),
                        "confidence": a.get("confidence"),
                        "desc": a.get("desc"),
                        "solution": a.get("solution"),
                        "reference": a.get("reference"),
                        "instances_count": len(a.get("instances", []) or []) if isinstance(a.get("instances"), list) else None,
                    }
                )

    return risk_counts, alerts_out


def _interpret_zap_packaged_exit_code(scan_level: ZapScanLevel, returncode: int) -> Dict[str, Any]:
    """
    Best-effort interpretation for packaged scan exit codes.

    Packaged scripts may use non-zero exit codes to signal findings / policy thresholds,
    not only "tool execution failure". For agent UX, we separate:
    - execution_status: did the tool run successfully?
    - scan_outcome: pass/warn/fail/unknown
    """
    # Conservative defaults
    out: Dict[str, Any] = {"exit_code": returncode, "execution_status": "unknown", "scan_outcome": "unknown"}

    if returncode == -1:
        out["execution_status"] = "error"
        out["scan_outcome"] = "unknown"
        return out

    # ZAP packaged scan scripts commonly use:
    # 0 = pass (no alerts at/above threshold), 1 = warn, 2 = fail
    # We treat all of these as successful execution.
    if returncode in (0, 1, 2):
        out["execution_status"] = "success"
        if returncode == 0:
            out["scan_outcome"] = "pass"
        elif returncode == 1:
            out["scan_outcome"] = "warn"
        elif returncode == 2:
            out["scan_outcome"] = "fail"
        return out

    # Any other non-zero: likely execution failure
    if returncode != 0:
        out["execution_status"] = "error"
        out["scan_outcome"] = "unknown"
    else:
        out["execution_status"] = "success"
        out["scan_outcome"] = "pass"
    return out


def _zap_image_from_env_or_default() -> str:
    """
    Select a ZAP Docker image.

    Preference order:
    1) Explicit env override: ZAP_DOCKER_IMAGE
    2) First locally-available image from known stable candidates
    3) Fallback to DockerHub stable alias used in docs
    """
    env_img = os.getenv("ZAP_DOCKER_IMAGE")
    if env_img:
        return env_img

    # Try picking an image that exists locally to avoid failures in restricted environments
    docker_runtime = "docker"
    client = get_docker_client()
    if client and getattr(client, "docker_runtime", None):
        docker_runtime = client.docker_runtime

    candidates = [
        # Docker Hub stable alias (docs show zaproxy/zap-stable)
        "zaproxy/zap-stable",
        # GHCR stable (docs show ghcr.io/zaproxy/zaproxy:stable)
        "ghcr.io/zaproxy/zaproxy:stable",
    ]

    for img in candidates:
        try:
            r = subprocess.run(
                [docker_runtime, "image", "inspect", img],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if r.returncode == 0:
                return img
        except Exception:
            # If docker isn't available or inspect fails, we fall back below
            continue

    return "zaproxy/zap-stable"


def _build_zap_args(
    scan_level: ZapScanLevel,
    target: str,
    report_json_name: str,
    report_html_name: str,
    baseline_spider_minutes: int,
    api_format: ApiFormat,
    api_spec_in_container: Optional[str],
) -> List[str]:
    # ZAP Docker guide documents packaged scans at a high level:
    # baseline/full/api scripts are available in the image.
    # https://www.zaproxy.org/docs/docker/about/
    if scan_level == "baseline":
        # -t target
        # -m minutes for spider (baseline default is 1 minute)
        # -J JSON report, -r HTML report
        return [
            "zap-baseline.py",
            "-t",
            target,
            "-m",
            str(baseline_spider_minutes),
            "-J",
            report_json_name,
            "-r",
            report_html_name,
        ]

    if scan_level == "full":
        return [
            "zap-full-scan.py",
            "-t",
            target,
            "-J",
            report_json_name,
            "-r",
            report_html_name,
        ]

    # api
    # Per ZAP API Scan docs, -t is the API definition (OpenAPI/SOAP URL or file) OR the GraphQL endpoint URL.
    # -u is for *config file URL*, not for the API definition itself.
    # Ref: https://www.zaproxy.org/docs/docker/api-scan/
    api_definition = api_spec_in_container or target
    args = [
        "zap-api-scan.py",
        "-t",
        api_definition,
        "-f",
        api_format,
        "-J",
        report_json_name,
        "-r",
        report_html_name,
    ]
    return args


@tool
def owasp_zap_scan(
    runtime: ToolRuntime,
    target: str,
    scan_level: ZapScanLevel = "baseline",
    baseline_spider_minutes: int = 1,
    api_format: ApiFormat = "openapi",
    api_spec: Optional[str] = None,
    timeout_seconds: int = 1800,
    max_alerts: int = 50,
    docker_image: Optional[str] = None,
    dry_run: bool = False,
    acknowledge_active_scan: bool = False,
    docker_tty: Optional[bool] = None,
) -> str:
    """
    Run OWASP ZAP packaged scans via Docker and return a structured JSON report.

    Args:
        runtime: ToolRuntime (injected by LangChain).
        target: http(s) target URL to scan.
        scan_level: "baseline" (default), "full", or "api".
        baseline_spider_minutes: spider duration for baseline scan (default 1).
        api_format: "openapi" (default) or "graphql" (api scans only).
        api_spec: Optional OpenAPI/GraphQL definition URL or local file path.
            - If provided and local file exists, it is mounted into /zap/wrk and passed to the scan script.
            - If provided and looks like a URL, it is passed as-is.
        timeout_seconds: Docker execution timeout (default 1800s).
        max_alerts: max number of alerts returned in the structured output (default 50).
        docker_image: Optional override for Docker image (defaults to env ZAP_DOCKER_IMAGE or zaproxy/zap-stable).
        dry_run: If True, does not execute Docker or perform any network activity; returns the planned
            docker image, arguments, and mount configuration for review (default: False).
        acknowledge_active_scan: Required for scan_level="full" since it performs active/intrusive scanning
            (default: False).
        docker_tty: Controls whether to pass `-t` to `docker run`. Defaults to auto-detect (isatty()).

    Returns:
        JSON string with:
        - status: "success" | "error"
        - scan_level, target
        - summary: counts by risk
        - alerts: limited list of alerts
        - report_json: (best-effort) raw parsed JSON report
        - artifacts: names of report files written inside mounted work dir
        - docker: basic execution metadata
    """
    try:
        # Validate
        err = _validate_target_url(target)
        if err:
            safe_log_error(logger, "[owasp_zap_scan] Validation failed", exc_info=False, error_msg=err)
            return json.dumps({"status": "error", "message": err})

        if scan_level not in ("baseline", "full", "api"):
            msg = "scan_level must be one of: baseline, full, api"
            safe_log_error(logger, "[owasp_zap_scan] Validation failed", exc_info=False, error_msg=msg, scan_level=scan_level)
            return json.dumps({"status": "error", "message": msg})

        if baseline_spider_minutes < 1 or baseline_spider_minutes > 60:
            msg = "baseline_spider_minutes must be between 1 and 60"
            safe_log_error(logger, "[owasp_zap_scan] Validation failed", exc_info=False, error_msg=msg, baseline_spider_minutes=baseline_spider_minutes)
            return json.dumps({"status": "error", "message": msg})

        if timeout_seconds < 30 or timeout_seconds > 24 * 3600:
            msg = "timeout_seconds must be between 30 and 86400"
            safe_log_error(logger, "[owasp_zap_scan] Validation failed", exc_info=False, error_msg=msg, timeout_seconds=timeout_seconds)
            return json.dumps({"status": "error", "message": msg})

        if max_alerts < 1 or max_alerts > 500:
            msg = "max_alerts must be between 1 and 500"
            safe_log_error(logger, "[owasp_zap_scan] Validation failed", exc_info=False, error_msg=msg, max_alerts=max_alerts)
            return json.dumps({"status": "error", "message": msg})

        if scan_level == "api" and api_format not in ("openapi", "graphql"):
            msg = "api_format must be one of: openapi, graphql"
            safe_log_error(logger, "[owasp_zap_scan] Validation failed", exc_info=False, error_msg=msg, api_format=api_format)
            return json.dumps({"status": "error", "message": msg})

        # Guardrails for intrusive scans
        if scan_level == "full" and not acknowledge_active_scan:
            msg = (
                "scan_level='full' performs active (intrusive) scanning. "
                "Set acknowledge_active_scan=true to proceed."
            )
            safe_log_error(logger, "[owasp_zap_scan] Active-scan acknowledgement required", exc_info=False, error_msg=msg)
            return json.dumps({"status": "error", "message": msg})

        safe_log_info(
            logger,
            "[owasp_zap_scan] Starting",
            target=target,
            scan_level=scan_level,
            baseline_spider_minutes=baseline_spider_minutes,
            api_format=api_format,
            api_spec_present=bool(api_spec),
            timeout_seconds=timeout_seconds,
            max_alerts=max_alerts,
            dry_run=dry_run,
        )

        # Build execution plan up front (used for dry_run too)
        image = docker_image or _zap_image_from_env_or_default()

        with tempfile.TemporaryDirectory(prefix="zap_wrk_") as tmpdir:
            workdir = Path(tmpdir)
            report_json_name = "zap_report.json"
            report_html_name = "zap_report.html"
            report_json_path = workdir / report_json_name
            report_html_path = workdir / report_html_name

            api_spec_in_container: Optional[str] = None
            if api_spec:
                api_spec = str(api_spec).strip()
                if _is_http_url(api_spec):
                    api_spec_in_container = api_spec
                else:
                    # Local path: copy into mounted /zap/wrk
                    spec_path = Path(api_spec)
                    if spec_path.exists() and spec_path.is_file():
                        dest_name = f"api_spec{spec_path.suffix or '.txt'}"
                        dest_path = workdir / dest_name
                        try:
                            dest_path.write_bytes(spec_path.read_bytes())
                            api_spec_in_container = f"/zap/wrk/{dest_name}"
                        except Exception as e:
                            msg = f"Failed to stage api_spec into ZAP workdir: {str(e)}"
                            safe_log_error(logger, "[owasp_zap_scan] api_spec staging failed", error_msg=msg, exc_info=True)
                            return json.dumps({"status": "error", "message": msg})
                    else:
                        # If not a URL and doesn't exist, treat as user error
                        msg = "api_spec must be an http(s) URL or an existing local file path"
                        safe_log_error(logger, "[owasp_zap_scan] Validation failed", exc_info=False, error_msg=msg, api_spec=api_spec)
                        return json.dumps({"status": "error", "message": msg})

            args = _build_zap_args(
                scan_level=scan_level,
                target=target,
                report_json_name=report_json_name,
                report_html_name=report_html_name,
                baseline_spider_minutes=baseline_spider_minutes,
                api_format=api_format,
                api_spec_in_container=api_spec_in_container,
            )

            volumes = [f"{str(workdir)}:/zap/wrk/:rw"]

            resolved_tty = docker_tty
            if resolved_tty is None:
                # In many automation contexts (CI, Cursor terminals), stdout isn't a TTY.
                # Passing -t can cause docker to fail with: "the input device is not a TTY".
                try:
                    resolved_tty = bool(sys.stdout.isatty())
                except Exception:
                    resolved_tty = False

            if dry_run:
                # Do NOT perform any network activity. Return an execution plan.
                return json.dumps(
                    {
                        "status": "success",
                        "dry_run": True,
                        "scan_level": scan_level,
                        "target": target,
                        "docker": {
                            "image": image,
                            "args": args,
                            "volumes": volumes,
                            "timeout_seconds": timeout_seconds,
                            "tty": resolved_tty,
                        },
                        "artifacts_expected": {
                            "json_report": report_json_name,
                            "html_report": report_html_name,
                        },
                        "notes": [
                            "Dry run mode: no docker execution was performed.",
                            "See ZAP Docker User Guide: https://www.zaproxy.org/docs/docker/about/",
                        ],
                    },
                    indent=2,
                )

        if not _check_docker_available():
            error_msg = (
                "Docker is required to run OWASP ZAP scans.\n"
                "1) Ensure Docker is running: docker ps\n"
                "2) Pull ZAP image (optional): docker pull zaproxy/zap-stable\n"
                "See: https://www.zaproxy.org/docs/docker/about/"
            )
            safe_log_error(logger, "[owasp_zap_scan] Docker not available", exc_info=False, error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})

        with tempfile.TemporaryDirectory(prefix="zap_wrk_") as tmpdir:
            workdir = Path(tmpdir)
            report_json_name = "zap_report.json"
            report_html_name = "zap_report.html"
            report_json_path = workdir / report_json_name
            report_html_path = workdir / report_html_name

            api_spec_in_container: Optional[str] = None
            if api_spec:
                api_spec = str(api_spec).strip()
                if _is_http_url(api_spec):
                    api_spec_in_container = api_spec
                else:
                    # Local path: copy into mounted /zap/wrk
                    spec_path = Path(api_spec)
                    if spec_path.exists() and spec_path.is_file():
                        dest_name = f"api_spec{spec_path.suffix or '.txt'}"
                        dest_path = workdir / dest_name
                        try:
                            dest_path.write_bytes(spec_path.read_bytes())
                            api_spec_in_container = f"/zap/wrk/{dest_name}"
                        except Exception as e:
                            msg = f"Failed to stage api_spec into ZAP workdir: {str(e)}"
                            safe_log_error(logger, "[owasp_zap_scan] api_spec staging failed", error_msg=msg, exc_info=True)
                            return json.dumps({"status": "error", "message": msg})
                    else:
                        # If not a URL and doesn't exist, treat as user error
                        msg = "api_spec must be an http(s) URL or an existing local file path"
                        safe_log_error(logger, "[owasp_zap_scan] Validation failed", exc_info=False, error_msg=msg, api_spec=api_spec)
                        return json.dumps({"status": "error", "message": msg})

            args = _build_zap_args(
                scan_level=scan_level,
                target=target,
                report_json_name=report_json_name,
                report_html_name=report_html_name,
                baseline_spider_minutes=baseline_spider_minutes,
                api_format=api_format,
                api_spec_in_container=api_spec_in_container,
            )

            safe_log_debug(logger, "[owasp_zap_scan] Executing Docker scan", image=image, args=args)
            docker_result = execute_official_docker_image(
                image=image,
                args=args,
                timeout=timeout_seconds,
                volumes=[f"{str(workdir)}:/zap/wrk/:rw"],
                env=None,
                platform=None,
                tty=bool(resolved_tty),
            )

            returncode = int(docker_result.get("returncode", -1))
            stdout = (docker_result.get("stdout") or "").strip()
            stderr = (docker_result.get("stderr") or "").strip()

            # Read reports (best effort)
            report_json = _read_json_if_exists(report_json_path)
            report_html_preview = _read_text_if_exists(report_html_path, max_chars=25_000)

            risk_counts, alerts = _summarize_zap_report(report_json, max_alerts=max_alerts)

            # Consider success even when alerts exist; treat returncode != 0 as error but still surface artifacts
            exit_meta = _interpret_zap_packaged_exit_code(scan_level=scan_level, returncode=returncode)
            # Tool-level status means "did the tool execute and produce outputs".
            # Findings / thresholds are represented by exit_meta.scan_outcome.
            status = "success" if exit_meta.get("execution_status") == "success" else "error"
            summary = {
                "alerts_by_risk": risk_counts,
                "alerts_returned": len(alerts),
                "alerts_total_in_report": sum(risk_counts.values()) if risk_counts else None,
            }

            # If report parsing failed, still provide helpful context
            if report_json is None:
                safe_log_debug(
                    logger,
                    "[owasp_zap_scan] No JSON report parsed",
                    report_json_exists=report_json_path.exists(),
                    stdout_len=len(stdout),
                    stderr_len=len(stderr),
                )

            safe_log_info(
                logger,
                "[owasp_zap_scan] Complete",
                target=target,
                scan_level=scan_level,
                returncode=returncode,
                alerts_returned=len(alerts),
                risks=list(risk_counts.keys()),
            )

            resp: Dict[str, Any] = {
                "status": status,
                "scan_level": scan_level,
                "target": target,
                "zap_exit": exit_meta,
                "summary": summary,
                "alerts": alerts,
                "report_json": report_json,
                "artifacts": {
                    "json_report": report_json_name if report_json_path.exists() else None,
                    "html_report": report_html_name if report_html_path.exists() else None,
                    "html_report_preview": report_html_preview,
                },
                "docker": {
                    "image": image,
                    "returncode": returncode,
                    "execution_time": docker_result.get("execution_time"),
                },
            }

            # On execution error, include a short stderr preview to make debugging actionable
            if status == "error" and returncode not in (0, 1, 2):
                resp["error"] = {
                    "message": docker_result.get("message") or "ZAP scan returned non-zero exit code",
                    "stderr_preview": (stderr[:4000] + "...[TRUNCATED]") if len(stderr) > 4000 else stderr,
                    "stdout_preview": (stdout[:2000] + "...[TRUNCATED]") if len(stdout) > 2000 else stdout,
                    "hint": (
                        "If your target is on localhost, Docker cannot reach it directly. "
                        "See ZAP Docker docs for 'Scanning an app running on the host OS'."
                    ),
                }

            return json.dumps(resp, indent=2)

    except Exception as e:
        safe_log_error(logger, "[owasp_zap_scan] Unexpected error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"OWASP ZAP scan failed: {str(e)}"})


