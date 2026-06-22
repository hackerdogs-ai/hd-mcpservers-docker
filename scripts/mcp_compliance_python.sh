# shellcheck shell=bash
# Resolve an interpreter for scripts/mcp_stdio_docker_tools_list.py (sourced by test.sh).
# Override with MCP_PYTHON=/path/to/python.exe

mcp_resolve_python() {
    if [ -n "${MCP_PYTHON:-}" ]; then
        return 0
    fi
    if command -v python3 >/dev/null 2>&1 && python3 -c "pass" >/dev/null 2>&1; then
        MCP_PYTHON=python3
        return 0
    fi
    if command -v python >/dev/null 2>&1 && python -c "pass" >/dev/null 2>&1; then
        MCP_PYTHON=python
        return 0
    fi
    _u="${USERNAME:-${USER:-}}"
    if [ -n "$_u" ]; then
        for _ver in 3.14 3.13 3.12 3.11; do
            _p="/c/Users/${_u}/AppData/Local/Python/pythoncore-${_ver}-64/python.exe"
            if [ -f "$_p" ]; then
                MCP_PYTHON="$_p"
                return 0
            fi
        done
    fi
    MCP_PYTHON=python3
    return 1
}

mcp_resolve_python || true
