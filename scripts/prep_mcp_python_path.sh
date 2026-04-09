#!/usr/bin/env bash
# Source from test.sh so `python3` works when run standalone in Git Bash on Windows
# (avoids the Windows Store "python3" app-execution-alias stub).
# Override install location:
#   MCP_WIN_PYTHON=/c/Users/you/.../python.exe bash test.sh
# Batch runners can keep prepending their own PATH shim instead of sourcing this.

MCP_TEST_PYTHON_BIN="${MCP_TEST_PYTHON_BIN:-/tmp/mcp-test-python-bin}"

_mcp_resolve_winpython() {
  local p
  for p in "${MCP_WIN_PYTHON:-}" \
    "/c/Users/${USER:-asus}/AppData/Local/Python/pythoncore-3.14-64/python.exe" \
    "/c/Users/${USER:-asus}/AppData/Local/Python/pythoncore-3.13-64/python.exe" \
    "/c/Users/${USER:-asus}/AppData/Local/Python/pythoncore-3.12-64/python.exe" \
    "/c/Users/${USER:-asus}/AppData/Local/Programs/Python/Python314/python.exe" \
    "/c/Users/${USER:-asus}/AppData/Local/Programs/Python/Python313/python.exe" \
    "/c/Users/${USER:-asus}/AppData/Local/Programs/Python/Python312/python.exe"; do
    [ -z "$p" ] && continue
    # Git Bash: .exe may not appear "executable" to -x; -f is enough for a real install
    [ -f "$p" ] || continue
    printf '%s\n' "$p"
    return 0
  done
  return 1
}

pyexe="$(_mcp_resolve_winpython || true)"
if [ -z "$pyexe" ]; then
  # Fallback: non–Windows-Store python3 already on PATH (e.g. pyenv, conda, custom install)
  _p="$(command -v python3 2>/dev/null || true)"
  if [ -n "$_p" ] && [[ "$_p" != *"/WindowsApps/"* ]] && [[ "$_p" != *"Microsoft\\WindowsApps"* ]]; then
    pyexe="$_p"
  fi
fi
if [ -n "$pyexe" ]; then
  mkdir -p "$MCP_TEST_PYTHON_BIN"
  printf '%s\n' '#!/usr/bin/env bash' "exec \"$pyexe\" \"\$@\"" >"$MCP_TEST_PYTHON_BIN/python3"
  chmod +x "$MCP_TEST_PYTHON_BIN/python3"
  export PATH="$MCP_TEST_PYTHON_BIN:$PATH"
fi
