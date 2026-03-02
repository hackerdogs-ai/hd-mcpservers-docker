"""DNSx MCP Server - Multi-purpose DNS Toolkit via FastMCP."""

import json
import os
import subprocess
import shutil
import tempfile
import sys
import logging

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("dnsx-mcp")

mcp = FastMCP(
    "dnsx-mcp",
    instructions="MCP server for DNSx - multi-purpose DNS toolkit for running queries (A, AAAA, CNAME, MX, TXT, NS, SOA, PTR) with wildcard handling, stats, and more.",
)

DNSX_BIN = shutil.which("dnsx") or "dnsx"

VALID_RECORD_TYPES = {"a", "aaaa", "cname", "ns", "mx", "txt", "ptr", "soa"}


def _run_dnsx(args: list[str], stdin_data: str | None = None, timeout: int = 120) -> dict:
    """Execute dnsx CLI and return structured result."""
    try:
        if stdin_data:
            result = subprocess.run(
                [DNSX_BIN] + args,
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        else:
            result = subprocess.run(
                [DNSX_BIN] + args,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            logger.warning("dnsx exited with code %d: %s", result.returncode, stderr)

        parsed = None
        if output:
            lines = output.splitlines()
            json_results = []
            for line in lines:
                try:
                    json_results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            if json_results:
                parsed = json_results
            elif not json_results:
                try:
                    parsed = json.loads(output)
                except json.JSONDecodeError:
                    pass

        return {
            "success": result.returncode == 0,
            "output": parsed if parsed is not None else output,
            "stderr": stderr if stderr else None,
            "exit_code": result.returncode,
        }
    except FileNotFoundError:
        logger.error("dnsx binary not found at '%s'", DNSX_BIN)
        return {
            "success": False,
            "output": None,
            "stderr": f"dnsx binary not found at '{DNSX_BIN}'. Ensure dnsx is installed.",
            "exit_code": -1,
        }
    except subprocess.TimeoutExpired:
        logger.error("dnsx command timed out after %ds", timeout)
        return {
            "success": False,
            "output": None,
            "stderr": f"dnsx command timed out after {timeout}s",
            "exit_code": -1,
        }
    except Exception as exc:
        logger.error("dnsx command failed: %s", exc)
        return {
            "success": False,
            "output": None,
            "stderr": str(exc),
            "exit_code": -1,
        }


@mcp.tool()
def resolve_domains(
    domains: str,
    record_types: list[str] | None = None,
    show_response: bool = True,
    response_only: bool = False,
    check_cdn: bool = False,
    check_asn: bool = False,
) -> dict:
    """Resolve DNS records for one or more domains.

    Queries DNS records for the provided domains using dnsx. Supports
    multiple record types (A, AAAA, CNAME, NS, MX, TXT, PTR, SOA).

    Args:
        domains: Domains to resolve, one per line or comma-separated (e.g. "example.com,google.com").
        record_types: List of record types to query. Options: a, aaaa, cname, ns, mx, txt, ptr, soa. Default queries A records.
        show_response: If True, display DNS response values. Default True.
        response_only: If True, show only response values without domain names. Default False.
        check_cdn: If True, detect CDN usage for domains. Default False.
        check_asn: If True, display ASN information. Default False.

    Returns:
        Dictionary with DNS resolution results.
    """
    logger.info("resolve_domains called with domains=%s", domains)
    domain_list = []
    for part in domains.replace(",", "\n").splitlines():
        part = part.strip()
        if part:
            domain_list.append(part)

    if not domain_list:
        return {"success": False, "output": None, "stderr": "No domains provided", "exit_code": -1}

    stdin_data = "\n".join(domain_list)
    args = ["-json"]

    if record_types:
        for rt in record_types:
            rt = rt.lower().strip()
            if rt in VALID_RECORD_TYPES:
                args.append(f"-{rt}")
    else:
        args.append("-a")

    if show_response:
        args.append("-resp")

    if response_only:
        args.append("-resp-only")

    if check_cdn:
        args.append("-cdn")

    if check_asn:
        args.append("-asn")

    return _run_dnsx(args, stdin_data=stdin_data)


@mcp.tool()
def bruteforce_subdomains(
    domain: str,
    wordlist_content: str,
    record_type: str = "a",
) -> dict:
    """Bruteforce subdomains using a wordlist.

    Performs DNS subdomain brute-forcing by combining the given domain with
    each word in the wordlist (e.g. word.domain.com) and resolving the result.

    Args:
        domain: Target domain to bruteforce subdomains for (e.g. "example.com").
        wordlist_content: Newline-separated list of subdomain words to try (e.g. "www\\nmail\\napi\\ndev").
        record_type: DNS record type to query. Default "a". Options: a, aaaa, cname, ns, mx, txt, ptr, soa.

    Returns:
        Dictionary with discovered subdomains and their DNS records.
    """
    logger.info("bruteforce_subdomains called with domain=%s", domain)
    if not domain.strip():
        return {"success": False, "output": None, "stderr": "No domain provided", "exit_code": -1}

    words = [w.strip() for w in wordlist_content.splitlines() if w.strip()]
    if not words:
        return {"success": False, "output": None, "stderr": "No wordlist content provided", "exit_code": -1}

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as wf:
            wf.write("\n".join(words))
            wordlist_path = wf.name

        args = ["-domain", domain.strip(), "-wordlist", wordlist_path, "-json"]

        rt = record_type.lower().strip()
        if rt in VALID_RECORD_TYPES:
            args.append(f"-{rt}")

        args.append("-resp")

        return _run_dnsx(args)
    finally:
        try:
            os.unlink(wordlist_path)
        except OSError:
            pass


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    port = int(os.environ.get("MCP_PORT", "8108"))
    logger.info("Starting dnsx-mcp server (transport=%s, port=%s)", transport, port)

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
