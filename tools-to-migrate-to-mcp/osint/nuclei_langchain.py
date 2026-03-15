"""
Nuclei Tool for LangChain Agents

Template-based vulnerability scanner using ProjectDiscovery Nuclei.
"""

import json
import re
import subprocess
from typing import Optional, List
from langchain.tools import tool, ToolRuntime
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug
from shared.modules.tools.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/nuclei_tool.log")


def _check_docker_available() -> bool:
    """Check if Docker is available for running Nuclei in container."""
    client = get_docker_client()
    if client is None:
        safe_log_debug(logger, "[nuclei_scan] Docker client is None")
    is_available = client.docker_available if client else False
    safe_log_debug(logger, "[nuclei_scan] Docker availability check", docker_available=is_available)
    return is_available


def _strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def _parse_nuclei_jsonl_output(stdout: str, target: str, limit: Optional[int], logger) -> str:
    """
    Parse Nuclei JSONL output into structured JSON array.
    
    Args:
        stdout: Raw JSONL output from Nuclei (one JSON object per line, may contain ANSI codes and info messages)
        target: Target that was scanned
        limit: Maximum number of findings to return
        logger: Logger instance
        
    Returns:
        JSON string with structured findings
    """
    try:
        # Strip ANSI escape codes first
        stdout_clean = _strip_ansi_codes(stdout)
        
        findings = []
        lines = stdout_clean.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip obvious non-JSON lines (Nuclei info messages)
            # These typically start with [INF], [WRN], [ERR], or are ASCII art
            if (line.startswith('[') and not line.startswith('{"')) or \
               line.startswith('__') or \
               line.startswith('projectdiscovery') or \
               'nuclei-templates' in line.lower() or \
               'templates loaded' in line.lower() or \
               'Scan completed' in line or \
               'Executing' in line or \
               'Targets loaded' in line:
                continue
            
            try:
                finding = json.loads(line)
                # Validate it's actually a finding object (has expected keys)
                if isinstance(finding, dict) and ('template-id' in finding or 'info' in finding or 'matched-at' in finding):
                    findings.append(finding)
            except json.JSONDecodeError:
                # Skip invalid JSON lines
                continue
        
        total_findings = len(findings)
        
        # Categorize findings: separate tech stack from vulnerabilities
        tech_stack_findings = []
        vulnerability_findings = []
        service_detection_findings = []
        
        for finding in findings:
            template_id = finding.get('template-id', '').lower()
            severity = finding.get('info', {}).get('severity', '').lower()
            
            # Tech stack detection (Wappalyzer)
            if 'tech-detect' in template_id or 'wappalyzer' in finding.get('info', {}).get('name', '').lower():
                tech_stack_findings.append(finding)
            # Vulnerabilities (critical, high, medium, low)
            elif severity in ['critical', 'high', 'medium', 'low']:
                vulnerability_findings.append(finding)
            # Service detection and other info findings
            else:
                service_detection_findings.append(finding)
        
        # Prioritize tech stack findings: always include them even if limit is reached
        # Apply limit to vulnerabilities and service detections, but keep all tech stack
        limited_vulns = vulnerability_findings
        limited_services = service_detection_findings
        
        if limit is not None and limit > 0:
            # Calculate how many non-tech findings we can include
            tech_count = len(tech_stack_findings)
            available_slots = max(0, limit - tech_count)
            
            if len(vulnerability_findings) + len(service_detection_findings) > available_slots:
                # Prioritize vulnerabilities over service detections
                if len(vulnerability_findings) <= available_slots:
                    limited_vulns = vulnerability_findings
                    limited_services = service_detection_findings[:available_slots - len(vulnerability_findings)]
                else:
                    limited_vulns = vulnerability_findings[:available_slots]
                    limited_services = []
                
                safe_log_info(logger, "[nuclei_scan] Applied limit to findings",
                             original_count=total_findings,
                             tech_stack_count=tech_count,
                             limited_count=len(tech_stack_findings) + len(limited_vulns) + len(limited_services))
        
        # Combine findings: tech stack first, then vulnerabilities, then service detections
        final_findings = tech_stack_findings + limited_vulns + limited_services
        
        # Build comprehensive summary
        if len(final_findings) == 0:
            summary = f"Scan completed successfully. No findings detected for {target}. This is a valid result - no retry needed."
        else:
            parts = []
            if tech_stack_findings:
                parts.append(f"{len(tech_stack_findings)} tech stack detection(s)")
            if limited_vulns:
                parts.append(f"{len(limited_vulns)} vulnerability finding(s)")
            if limited_services:
                parts.append(f"{len(limited_services)} service detection(s)")
            
            summary_parts = ", ".join(parts)
            limit_msg = f" (showing top {limit} of {total_findings} total)" if limit is not None and total_findings > limit else ""
            summary = f"Found {summary_parts}{limit_msg}"
        
        result = {
            "status": "success",
            "target": target,
            "findings": final_findings,
            "tech_stack": tech_stack_findings,  # Explicit tech stack section for LLM
            "vulnerabilities": limited_vulns,  # Explicit vulnerabilities section
            "service_detections": limited_services,  # Service detections
            "count": len(final_findings),
            "total_found": total_findings,
            "summary": summary
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        safe_log_error(logger, "[nuclei_scan] Error parsing JSONL output",
                      error=str(e), exc_info=True)
        # Fallback: return structured error response instead of raw stdout with ANSI codes
        return json.dumps({
            "status": "error",
            "target": target,
            "findings": [],
            "count": 0,
            "total_found": 0,
            "summary": f"Error parsing Nuclei output: {str(e)}. Raw output may contain ANSI codes or non-JSON messages.",
            "error": str(e)
        }, indent=2)


@tool
def nuclei_scan(
    runtime: ToolRuntime,
    target: str,
    templates: Optional[List[str]] = None,
    severity: Optional[str] = None,
    tags: Optional[List[str]] = None,
    rate_limit: Optional[int] = None,
    concurrency: Optional[int] = None,
    limit: Optional[int] = 50
) -> str:
    """
    Scan target for vulnerabilities using Nuclei templates.
    
    Nuclei is a fast vulnerability scanner based on templates.
    It can detect CVEs, misconfigurations, and security issues.
    
    Best practices:
    - Automatic scan (-as) is enabled by default for intelligent template selection
    - Use rate limiting to avoid overwhelming targets
    - Filter by severity to focus on critical issues (default: critical,high,info - includes tech stack detection)
    - Use specific templates for targeted scanning (overrides automatic scan)
    - Regularly update templates: nuclei -update-templates
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: URL or IP to scan (e.g., "https://example.com" or "192.168.1.1").
        templates: Specific template IDs to use (default: all templates).
        severity: Filter by severity level. Options: "info", "low", "medium", "high", "critical".
                  Can specify multiple: "critical,high" (default: "critical,high,info" - includes tech stack detection).
        tags: Filter by template tags (e.g., ["cve", "xss", "sqli"]).
        rate_limit: Maximum requests per second (default: None, uses Nuclei default).
                    Recommended: 50-150 for production targets.
        concurrency: Number of concurrent requests (default: None, uses Nuclei default).
                     Recommended: 25-50 for most targets.
        limit: Maximum number of findings to return (default: 50).
               Recommended: 50-100 to keep output manageable for LLM.
               Set to None to return all findings (not recommended for large scans).
    
    Returns:
        JSON string with vulnerability findings including:
        - status: "success" or "error"
        - target: Scanned target
        - findings: List of vulnerability findings (limited if limit specified)
        - count: Number of findings returned
        - total_found: Total number of findings before limit
        - summary: Summary message
    """
    try:
        # Default severity to critical,high,info if not specified or empty
        # Includes critical/high vulnerabilities AND info findings (tech stack, service detection, etc.)
        if not severity or (isinstance(severity, str) and len(severity.strip()) == 0):
            severity = "critical,high,info"
        
        safe_log_info(logger, "[nuclei_scan] Starting scan", 
                     target=target,
                     templates=templates,
                     severity=severity,
                     tags=tags,
                     rate_limit=rate_limit,
                     concurrency=concurrency,
                     limit=limit)
        
        # Validate inputs
        if not target or not isinstance(target, str) or len(target.strip()) == 0:
            error_msg = "target must be a non-empty string"
            safe_log_error(logger, "[nuclei_scan] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        target = target.strip()
        
        # Validate severity (can be comma-separated like "critical,high")
        # Severity should always be set at this point (default or user-provided)
        if severity:
            severity_list = [s.strip().lower() for s in severity.split(",")]
            # Filter out empty strings from split
            severity_list = [s for s in severity_list if s]
            valid_severities = ["info", "low", "medium", "high", "critical"]
            invalid = [s for s in severity_list if s not in valid_severities]
            if invalid:
                error_msg = f"severity must be one or more of: info, low, medium, high, critical (got invalid: {invalid})"
                safe_log_error(logger, "[nuclei_scan] Validation failed", error_msg=error_msg, severity=severity)
                return json.dumps({"status": "error", "message": error_msg})
        
        if rate_limit is not None and (rate_limit < 1 or rate_limit > 10000):
            error_msg = "rate_limit must be between 1 and 10000"
            safe_log_error(logger, "[nuclei_scan] Validation failed", error_msg=error_msg, rate_limit=rate_limit)
            return json.dumps({"status": "error", "message": error_msg})
        
        if concurrency is not None and (concurrency < 1 or concurrency > 1000):
            error_msg = "concurrency must be between 1 and 1000"
            safe_log_error(logger, "[nuclei_scan] Validation failed", error_msg=error_msg, concurrency=concurrency)
            return json.dumps({"status": "error", "message": error_msg})
        
        if limit is not None:
            if limit < 1 or limit > 1000:
                error_msg = "limit must be between 1 and 1000"
                safe_log_error(logger, "[nuclei_scan] Validation failed", error_msg=error_msg, limit=limit)
                return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[nuclei_scan] Inputs validated", target=target)
        
        # Docker-only execution
        if not _check_docker_available():
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                "2. Start container: docker-compose up -d"
            )
            safe_log_error(logger, "[nuclei_scan] Docker not available", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Build Nuclei command arguments
        # Reference: https://docs.projectdiscovery.io/opensource/nuclei/usage
        # Use -jsonl flag for JSON Lines output format (one JSON object per line)
        # Use -as (automatic-scan) to enable automatic template selection based on target technology stack
        # Use -silent to suppress info messages and only output JSON findings
        args = ["-u", target, "-as", "-silent", "-jsonl", "-o", "-"]
        
        # Template selection
        if templates:
            args.extend(["-t", ",".join(templates)])
        
        # Severity filtering (e.g., "critical,high" or "critical")
        if severity:
            args.extend(["-severity", severity])
        
        # Tag filtering
        if tags:
            args.extend(["-tags", ",".join(tags)])
        
        # Rate limiting (requests per second)
        if rate_limit:
            args.extend(["-rate-limit", str(rate_limit)])
        
        # Concurrency control
        if concurrency:
            args.extend(["-c", str(concurrency)])
        
        # Execute in Docker (uses official projectdiscovery/nuclei image if available)
        safe_log_info(logger, "[nuclei_scan] Executing in Docker", target=target, timeout=600, args=args)
        docker_result = execute_in_docker("nuclei", args, timeout=600)
        
        # Nuclei exit codes:
        # 0 = Success, no findings
        # 1 = Success, findings found (not an error)
        # >1 = Actual error
        # -1 = Timeout or Docker error (from docker_client)
        returncode = docker_result.get("returncode", -1)
        stdout = docker_result.get("stdout", "")
        stderr = docker_result.get("stderr", "")
        
        # Check for Docker errors (timeout, Docker not found, etc.)
        if docker_result.get("status") == "error" and returncode == -1:
            error_msg = docker_result.get("message", "Docker execution failed")
            safe_log_error(logger, "[nuclei_scan] Docker execution error", 
                         error=error_msg,
                         returncode=returncode,
                         target=target)
            return json.dumps({"status": "error", "message": error_msg, "returncode": returncode})
        
        # Check for errors (returncode > 1 indicates actual error, not just "no findings")
        if returncode > 1:
            # Build comprehensive error message
            error_parts = [f"Nuclei scan failed (returncode: {returncode})"]
            if stderr and stderr.strip():
                error_parts.append(f"stderr: {stderr.strip()}")
            if stdout and stdout.strip():
                # Sometimes errors are in stdout
                error_parts.append(f"stdout: {stdout.strip()[:500]}")  # Limit stdout in error
            if docker_result.get("message"):
                error_parts.append(f"message: {docker_result.get('message')}")
            
            error_msg = ". ".join(error_parts) if len(error_parts) > 1 else error_parts[0]
            
            safe_log_error(logger, "[nuclei_scan] Execution failed", 
                         error=error_msg,
                         returncode=returncode,
                         target=target,
                         stderr=stderr[:500] if stderr else None,
                         stdout_preview=stdout[:200] if stdout else None,
                         args=args)
            return json.dumps({"status": "error", "message": error_msg, "returncode": returncode})
        
        safe_log_info(logger, "[nuclei_scan] Complete", 
                     target=target,
                     returncode=returncode,
                     output_length=len(stdout) if stdout else len(stderr))
        
        # Parse JSONL output into structured JSON
        # Even if stdout is empty, try parsing (will return empty findings)
        if stdout and stdout.strip():
            parsed_output = _parse_nuclei_jsonl_output(stdout, target, limit, logger)
            safe_log_info(logger, "[nuclei_scan] Parsed output", 
                         target=target,
                         output_length=len(parsed_output))
            return parsed_output
        else:
            # No findings (returncode 0) or empty stdout
            # Check if stderr has important messages
            if stderr and stderr.strip():
                # Log stderr but don't treat as error if returncode is 0 or 1
                safe_log_debug(logger, "[nuclei_scan] Stderr output (non-error)", stderr=stderr, returncode=returncode)
            
            return json.dumps({
                "status": "success",
                "target": target,
                "findings": [],
                "count": 0,
                "total_found": 0,
                "summary": f"Scan completed successfully. No vulnerabilities found for {target} with severity filter: {severity}. This is a valid result - no retry needed."
            }, indent=2)
        
    except Exception as e:
        safe_log_error(logger, "[nuclei_scan] Error", 
                     exc_info=True,
                     error=str(e),
                     target=target if 'target' in locals() else None)
        return json.dumps({"status": "error", "message": f"Nuclei scan failed: {str(e)}"})

