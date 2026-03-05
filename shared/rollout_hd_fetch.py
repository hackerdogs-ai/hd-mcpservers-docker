#!/usr/bin/env python3
"""Rollout script: add hd_fetch URL download capability to MCP tool servers.

Strategy: since all generic-argument tools follow an identical code pattern,
we match the *entire* run_<tool> function via regex and replace it with
the updated version that includes source_url handling and try/finally cleanup.
"""

import os
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SHARED_DIR = REPO_ROOT / "shared"
HD_FETCH_SRC = SHARED_DIR / "hd_fetch.py"

GENERIC_TOOLS = [
    "trufflehog-mcp", "checkov-mcp", "terrascan-mcp", "gitleaks-mcp",
    "horusec-mcp", "bearer-mcp", "dependency-check-mcp", "kubescape-mcp",
    "ggshield-mcp", "retire-js-mcp",
    "peda-mcp", "gef-mcp", "radare2-mcp", "ghidra-mcp",
    "ropgadget-mcp", "ropper-mcp", "checksec-mcp", "pwntools-mcp",
    "angr-mcp", "one-gadget-mcp", "libc-database-mcp", "pwninit-mcp",
    "upx-mcp", "cutter-mcp",
    "volatility3-mcp", "volatility-mcp",
    "foremost-mcp", "steghide-mcp", "testdisk-mcp",
    "trivy-mcp", "trivy-neutr0n-mcp", "grype-mcp", "syft-mcp",
    "clair-mcp", "aibom-mcp",
    "yara-mcp", "capa-mcp", "yaraflux-mcp",
    "john-mcp", "hashcat-mcp", "hashpump-mcp",
    "wireshark-mcp",
    "docker-bench-security-mcp", "lynis-mcp", "kube-bench-mcp",
    "gobuster-mcp", "dirb-mcp", "dirsearch-mcp", "feroxbuster-mcp",
    "jaeles-mcp", "falco-mcp", "suricata-mcp",
]

OK = 0
SKIPPED = 0
ERRORS = 0


def _copy_hd_fetch(tool_dir: Path):
    shutil.copy2(HD_FETCH_SRC, tool_dir / "hd_fetch.py")


def _add_import(content: str) -> str:
    if "import hd_fetch" in content:
        return content
    return content.replace(
        "from fastmcp import FastMCP",
        "from fastmcp import FastMCP\nimport hd_fetch",
    )


def _extract_run_func_info(content: str) -> dict | None:
    """Extract the run function name and the CLI tool name for replacement."""
    m = re.search(
        r'@mcp\.tool\(\)\n'
        r'(async )?def (run_\w+)\(\n'
        r'    arguments: str,\n'
        r'    timeout_seconds: int = (\d+),\n'
        r'\) -> str:\n'
        r'    """Run (\S+) with the given arguments\.\n'
        r'\n'
        r'    Pass arguments as you would on the command line\.\n'
        r'\n'
        r'    Args:\n'
        r'        arguments: Command-line arguments string\.\n'
        r'        timeout_seconds: Maximum execution time in seconds \(default (\d+)\)\.\n'
        r'    """\n'
        r'    import shlex\n'
        r'\n'
        r'    logger\.info\("(run_\w+) called with arguments=%s", arguments\)\n'
        r'    args = shlex\.split\(arguments\) if arguments\.strip\(\) else \[\]\n'
        r'    result = await _run_command\(args, timeout_seconds=timeout_seconds\)\n'
        r'\n'
        r'    if result\["return_code"\] != 0:\n'
        r'        logger\.warning\("(\S+) command failed with exit code %d", result\["return_code"\]\)\n'
        r'        error_detail = result\["stderr"\] or result\["stdout"\] or "Unknown error"\n'
        r'        return json\.dumps\(\n'
        r'            \{\n'
        r'                "error": True,\n'
        r'                "message": f"(\S+) failed \(exit code \{result\[\'return_code\'\]\}\)",\n'
        r'                "detail": error_detail\.strip\(\),\n'
        r'                "command": f"(\S+) \{' + "' '" + r'\.join\(args\)\}",\n'
        r'            \},\n'
        r'            indent=2,\n'
        r'        \)\n'
        r'\n'
        r'    stdout = result\["stdout"\]\.strip\(\)\n'
        r'\n'
        r'    if not stdout:\n'
        r'        return json\.dumps\(\{"message": "Command completed with no output", "arguments": arguments\}\)\n'
        r'\n'
        r'    (?:# Try to parse as JSON/JSONL\n    )?results = \[\]\n'
        r'    for line in stdout\.splitlines\(\):\n'
        r'        line = line\.strip\(\)\n'
        r'        if not line:\n'
        r'            continue\n'
        r'        try:\n'
        r'            results\.append\(json\.loads\(line\)\)\n'
        r'        except json\.JSONDecodeError:\n'
        r'            results\.append\(\{"raw": line\}\)\n'
        r'\n'
        r'    if len\(results\) == 1:\n'
        r'        return json\.dumps\(results\[0\], indent=2\)\n'
        r'    return json\.dumps\(results, indent=2\)\n',
        content,
    )
    if not m:
        return None

    return {
        "is_async": m.group(1) is not None,
        "func_name": m.group(2),
        "timeout": m.group(3),
        "cli_name": m.group(4),
        "log_func": m.group(6),
        "warn_name": m.group(7),
        "err_name": m.group(8),
        "cmd_name": m.group(9),
        "full_match": m.group(0),
        "start": m.start(),
        "end": m.end(),
    }


def _build_new_run_func(info: dict) -> str:
    """Build the complete replacement run function with source_url support."""
    async_prefix = "async " if info["is_async"] else ""
    fn = info["func_name"]
    timeout = info["timeout"]
    cli = info["cli_name"]
    warn = info["warn_name"]
    err = info["err_name"]
    cmd = info["cmd_name"]

    return f'''@mcp.tool()
{async_prefix}def {fn}(
    arguments: str,
    source_url: str = "",
    timeout_seconds: int = {timeout},
) -> str:
    """Run {cli} with the given arguments.

    Pass arguments as you would on the command line.  Use ``source_url`` to
    have the server download files from a URL before processing.

    Args:
        arguments: Command-line arguments string.  Use ``{{source}}`` as a
                   placeholder for the downloaded file path when using
                   *source_url*.
        source_url: Optional HTTP(S) URL, GitHub/GitLab repo URL, or archive
                    URL.  Downloaded into the container; local path replaces
                    ``{{source}}`` in *arguments* or is appended.
        timeout_seconds: Maximum execution time in seconds (default {timeout}).
    """
    import shlex

    logger.info("{fn} called with arguments=%s source_url=%s", arguments, source_url)

    job_info = None
    try:
        if source_url:
            try:
                job_info = hd_fetch.fetch(source_url)
            except hd_fetch.FetchError as exc:
                return json.dumps({{"error": True, "message": str(exc)}}, indent=2)
            if "{{source}}" in arguments:
                arguments = arguments.replace("{{source}}", job_info["path"])
            else:
                arguments = f"{{arguments}} {{job_info[\'path\']}}".strip()

        args = shlex.split(arguments) if arguments.strip() else []
        result = await _run_command(args, timeout_seconds=timeout_seconds)

        if result["return_code"] != 0:
            logger.warning("{warn} command failed with exit code %d", result["return_code"])
            error_detail = result["stderr"] or result["stdout"] or "Unknown error"
            return json.dumps(
                {{
                    "error": True,
                    "message": f"{err} failed (exit code {{result[\'return_code\']}})",
                    "detail": error_detail.strip(),
                    "command": f"{cmd} {{' '.join(args)}}",
                }},
                indent=2,
            )

        stdout = result["stdout"].strip()

        if not stdout:
            return json.dumps({{"message": "Command completed with no output", "arguments": arguments}})

        results = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                results.append({{"raw": line}})

        if len(results) == 1:
            return json.dumps(results[0], indent=2)
        return json.dumps(results, indent=2)
    finally:
        if job_info:
            hd_fetch.cleanup(job_info["job_id"])
'''


def _build_download_tools(is_async: bool) -> str:
    if is_async:
        return '''

@mcp.tool()
async def download_file(
    url: str,
    extract: bool = True,
) -> str:
    """Download a file or repository from a URL into the container workspace.

    Use this to pre-download files before analysis, or when you need to
    download once and run multiple analyses on the same content.

    Args:
        url: HTTP(S) URL, GitHub/GitLab repo URL, or data: URI.
        extract: If True (default), automatically extract archives (.zip, .tar.gz, etc.).

    Returns:
        JSON with 'path' (local path to use in other tools) and
        'job_id' (use with cleanup_downloads to free space).
    """
    try:
        info = hd_fetch.fetch(url, extract=extract)
        return json.dumps(info, indent=2)
    except hd_fetch.FetchError as exc:
        return json.dumps({"error": True, "message": str(exc)}, indent=2)


@mcp.tool()
async def cleanup_downloads(job_id: str = "") -> str:
    """Clean up downloaded files from the container workspace.

    Args:
        job_id: Specific job ID to clean up.  If empty, removes all downloads.

    Returns:
        JSON confirming the cleanup.
    """
    if job_id:
        hd_fetch.cleanup(job_id)
        return json.dumps({"cleaned": job_id})
    hd_fetch.cleanup_all()
    return json.dumps({"cleaned": "all"})

'''
    else:
        return '''

@mcp.tool()
def download_file(
    url: str,
    extract: bool = True,
) -> dict:
    """Download a file or repository from a URL into the container workspace.

    Use this to pre-download files before analysis, or when you need to
    download once and run multiple analyses on the same content.

    Args:
        url: HTTP(S) URL, GitHub/GitLab repo URL, or data: URI.
        extract: If True (default), automatically extract archives (.zip, .tar.gz, etc.).

    Returns:
        Dictionary with 'path' (local path to use in other tools) and
        'job_id' (use with cleanup_downloads to free space).
    """
    try:
        return hd_fetch.fetch(url, extract=extract)
    except hd_fetch.FetchError as exc:
        return {"error": True, "message": str(exc)}


@mcp.tool()
def cleanup_downloads(job_id: str = "") -> dict:
    """Clean up downloaded files from the container workspace.

    Args:
        job_id: Specific job ID to clean up.  If empty, removes all downloads.

    Returns:
        Dictionary confirming the cleanup.
    """
    if job_id:
        hd_fetch.cleanup(job_id)
        return {"cleaned": job_id}
    hd_fetch.cleanup_all()
    return {"cleaned": "all"}

'''


def _update_generic_mcp_server(tool_dir: Path) -> bool:
    server_py = tool_dir / "mcp_server.py"
    content = server_py.read_text()

    if "import hd_fetch" in content and "def download_file(" in content:
        return True

    content = _add_import(content)

    info = _extract_run_func_info(content)
    if not info:
        print(f"  WARNING: could not match run function pattern in {server_py}")
        return False

    new_func = _build_new_run_func(info)
    content = content[:info["start"]] + new_func + content[info["end"]:]

    if "def download_file(" not in content:
        main_m = re.search(r'\ndef main\(\)', content)
        if main_m:
            dl_tools = _build_download_tools(info["is_async"])
            content = content[:main_m.start()] + dl_tools + content[main_m.start():]

    server_py.write_text(content)
    return True


def _update_dockerfile(tool_dir: Path) -> bool:
    dockerfile = tool_dir / "Dockerfile"
    if not dockerfile.exists():
        return False

    content = dockerfile.read_text()
    changed = False

    if "COPY hd_fetch.py" not in content:
        content = content.replace(
            "COPY mcp_server.py ./",
            "COPY mcp_server.py ./\nCOPY hd_fetch.py ./",
        )
        changed = True

    if "    git \\" not in content and "\ngit \\" not in content:
        m = re.search(r'(    tini \\\n)', content)
        if m:
            content = content.replace(m.group(1), m.group(1) + "    git \\\n", 1)
            changed = True

    if "unzip" not in content:
        m = re.search(r'(    tini \\\n(?:    git \\\n)?)', content)
        if m:
            content = content.replace(m.group(1), m.group(1) + "    unzip \\\n", 1)
            changed = True

    if "/app/workdir" not in content:
        if "mkdir -p /app/output" in content:
            content = content.replace(
                "mkdir -p /app/output",
                "mkdir -p /app/output /app/workdir",
            )
            changed = True
        elif re.search(r"mkdir -p /app/\w+", content):
            m = re.search(r"(mkdir -p /app/\w+)", content)
            content = content.replace(m.group(1), m.group(1) + " /app/workdir", 1)
            changed = True
        else:
            m = re.search(r'(USER mcpuser)', content)
            if m:
                content = content.replace(
                    m.group(0),
                    "RUN mkdir -p /app/workdir && chown mcpuser:mcpuser /app/workdir\n\n" + m.group(0),
                )
                changed = True

    if changed:
        dockerfile.write_text(content)
    return True


def rollout_tool(tool_name: str) -> bool:
    global OK, SKIPPED, ERRORS
    tool_dir = REPO_ROOT / tool_name
    if not tool_dir.is_dir():
        print(f"  SKIP: {tool_name} not found")
        SKIPPED += 1
        return False

    print(f"  Processing {tool_name}...", end="")
    try:
        _copy_hd_fetch(tool_dir)
        ok = _update_generic_mcp_server(tool_dir)
        if not ok:
            print(" FAILED (mcp_server.py)")
            ERRORS += 1
            return False
        _update_dockerfile(tool_dir)
        print(" OK")
        OK += 1
        return True
    except Exception as exc:
        print(f" ERROR: {exc}")
        ERRORS += 1
        return False


def main():
    if not HD_FETCH_SRC.exists():
        print(f"ERROR: {HD_FETCH_SRC} not found")
        sys.exit(1)

    print(f"Rolling out hd_fetch to {len(GENERIC_TOOLS)} generic tools...\n")

    for tool in GENERIC_TOOLS:
        rollout_tool(tool)

    print(f"\n{'='*50}")
    print(f"Results: {OK} updated, {SKIPPED} skipped, {ERRORS} errors")
    print(f"{'='*50}")

    if ERRORS:
        sys.exit(1)


if __name__ == "__main__":
    main()
