# shellcheck shell=bash
# Common bootstrap sourced (optionally) by per-server test.sh scripts.
# Resolves a Python interpreter into MCP_PYTHON for the stdio probe and sets
# sane defaults for the HTTP streamable probe timing. Safe to source more than once.
_BOOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=/dev/null
[ -f "${_BOOT_DIR}/mcp_compliance_python.sh" ] && . "${_BOOT_DIR}/mcp_compliance_python.sh"

# Fallback resolution if the compliance helper was not present.
if [ -z "${MCP_PYTHON:-}" ]; then
    if command -v python3 >/dev/null 2>&1; then MCP_PYTHON=python3
    elif command -v python  >/dev/null 2>&1; then MCP_PYTHON=python
    fi
fi

# HTTP streamable probe timing (overridable per server / per environment).
: "${MCP_HTTP_STARTUP_SLEEP:=10}"
: "${MCP_HTTP_LIST_MAX_WAIT:=45}"

export MCP_PYTHON MCP_HTTP_STARTUP_SLEEP MCP_HTTP_LIST_MAX_WAIT
