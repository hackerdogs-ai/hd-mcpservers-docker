#!/usr/bin/env bash
# =============================================================================
# Start MCP Farm locally (Docker backend + optional Vite UI dev server)
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERR]${NC}  $*"; exit 1; }

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCPFARM_DIR="$REPO_DIR/mcpfarm"
UI_DIR="$REPO_DIR/mcpfarm-ui"
RUN_DIR="$REPO_DIR/.mcpfarm"
VITE_PID_FILE="$RUN_DIR/vite.pid"
VITE_LOG_FILE="$RUN_DIR/vite.log"

FARM_PORT="${FARM_PORT:-8485}"
UI_DEV_PORT="${UI_DEV_PORT:-5173}"
FARM_HTTP="http://localhost:${FARM_PORT}"

DO_BUILD=false
DOCKER_UI=false
START_SERVERS=false
SERVERS=""
DO_STOP=false
FOREGROUND=false

DEFAULT_SERVERS=(nmap-mcp whois-mcp nuclei-mcp shodan-mcp)

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Start the MCP Farm locally: Docker backend (Caddy + auth-gateway) and,
by default, a Vite UI dev server in the background. Does not rebuild
Docker images unless you pass --build.

Options:
  -h, --help           Show this help and exit
  -f, --foreground     Run the UI dev server in the foreground (logs in terminal)
  --build              Build auth-gateway and mcpfarm-ui images before starting
  --docker-ui          Serve the production UI from Docker on FARM_PORT (no Vite)
  --start-servers      Also start a default MCP server set
  --servers LIST       Comma-separated MCP servers to start (e.g. nmap-mcp,whois-mcp)
  --stop               Stop infra containers and the background Vite dev server

Environment:
  FARM_PORT=8485       Caddy / API port (default: 8485)
  UI_DEV_PORT=5173     Vite dev server port (default: 5173)
  ADMIN_SECRET=        Optional. Leave empty to create via UI Generate on first open.
                       Set only if you need headless /admin curl without the UI.

Examples:
  $(basename "$0")                          # start without rebuilding (default)
  $(basename "$0") -f                       # same, Vite attached to terminal
  $(basename "$0") --build                  # rebuild images, then start
  $(basename "$0") --build --docker-ui      # rebuild + production UI only on :8485
  $(basename "$0") --start-servers          # also start nmap/whois/nuclei/shodan
  $(basename "$0") --stop                     # stop local farm

Files:
  $VITE_PID_FILE   Background Vite PID (dev mode)
  $VITE_LOG_FILE   Background Vite logs (dev mode)
  mcpfarm/.env     Local secrets and port config
EOF
  exit 0
}

vite_running() {
  [[ -f "$VITE_PID_FILE" ]] || return 1
  local pid
  pid="$(cat "$VITE_PID_FILE" 2>/dev/null)" || return 1
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

stop_vite() {
  if vite_running; then
    local pid
    pid="$(cat "$VITE_PID_FILE")"
    info "Stopping Vite dev server (pid ${pid})..."
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 10); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.3
    done
    kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$VITE_PID_FILE"
}

start_vite_daemon() {
  mkdir -p "$RUN_DIR"
  cd "$UI_DIR"

  if vite_running; then
    warn "Vite already running (pid $(cat "$VITE_PID_FILE")) — skipping start"
    return 0
  fi

  if [[ ! -d node_modules ]]; then
    npm ci
  fi

  export FARM_PORT UI_DEV_PORT
  info "Starting Vite dev server in background on http://localhost:${UI_DEV_PORT} ..."
  nohup ./node_modules/.bin/vite >>"$VITE_LOG_FILE" 2>&1 &
  echo $! >"$VITE_PID_FILE"

  for _ in $(seq 1 20); do
    if curl -sf "http://localhost:${UI_DEV_PORT}/" >/dev/null 2>&1; then
      success "Vite started (pid $(cat "$VITE_PID_FILE"), log: ${VITE_LOG_FILE})"
      return 0
    fi
    if ! kill -0 "$(cat "$VITE_PID_FILE")" 2>/dev/null; then
      error "Vite failed to start — see ${VITE_LOG_FILE}"
    fi
    sleep 0.5
  done
  success "Vite started (pid $(cat "$VITE_PID_FILE"), log: ${VITE_LOG_FILE})"
}

start_vite_foreground() {
  cd "$UI_DIR"
  if [[ ! -d node_modules ]]; then
    npm ci
  fi
  export FARM_PORT UI_DEV_PORT
  info "Starting Vite dev server in foreground on http://localhost:${UI_DEV_PORT} ..."
  info "Press Ctrl+C to stop the UI (Docker backend keeps running)"
  trap 'stop_vite; exit 0' INT TERM
  npm run dev
}

reload_routes() {
  if [[ -z "${ADMIN_SECRET:-}" ]]; then
    warn "ADMIN_SECRET unset — skip route reload (Generate it in the UI, then reload from Settings or: curl -X POST ${FARM_HTTP}/admin/reload -H \"X-Admin-Secret: …\")"
    return 0
  fi
  info "Reloading Caddy routes (UI → ${UI_UPSTREAM})..."
  local reload
  reload=$(curl -s -X POST "${FARM_HTTP}/admin/reload" \
    -H "X-Admin-Secret: ${ADMIN_SECRET}" 2>&1 || true)
  if echo "$reload" | grep -q "reloaded"; then
    success "Routes loaded"
  else
    warn "Route reload: ${reload:-no response} (may settle on next request)"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)        usage ;;
    -f|--foreground)  FOREGROUND=true; shift ;;
    --build)          DO_BUILD=true; shift ;;
    --docker-ui)      DOCKER_UI=true; shift ;;
    --start-servers)  START_SERVERS=true; shift ;;
    --stop)           DO_STOP=true; shift ;;
    --servers)
      shift
      SERVERS="${1:-}"
      [[ -z "$SERVERS" ]] && error "--servers requires a comma-separated list"
      shift
      ;;
    --servers=*)
      SERVERS="${1#*=}"
      [[ -z "$SERVERS" ]] && error "--servers requires a comma-separated list"
      shift
      ;;
    *)
      error "Unknown option: $1 (try --help)"
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Stop mode
# ---------------------------------------------------------------------------
if [[ "$DO_STOP" == "true" ]]; then
  stop_vite
  info "Stopping MCP Farm infra containers..."
  cd "$MCPFARM_DIR"
  docker compose stop caddy auth-gateway mcpfarm-ui 2>/dev/null || true
  success "Local MCP Farm stopped (individual *-mcp containers were left running)"
  exit 0
fi

echo ""
echo "============================================================"
echo "   Hackerdogs MCP Farm — Local Dev"
echo "============================================================"
echo ""

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------
info "Checking prerequisites..."
command -v docker  &>/dev/null || error "Docker not found."
docker info &>/dev/null        || error "Docker daemon not running."
command -v python3 &>/dev/null || error "python3 not found."

if [[ "$DOCKER_UI" == "false" ]]; then
  command -v node &>/dev/null || error "Node.js not found (required for UI dev server)."
  command -v npm  &>/dev/null || error "npm not found."
fi
success "Prerequisites OK"

mkdir -p "$MCPFARM_DIR/build-logs" "$RUN_DIR"

# ---------------------------------------------------------------------------
# .env
# ---------------------------------------------------------------------------
ENV_FILE="$MCPFARM_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  cat > "$ENV_FILE" <<EOF
# Leave ADMIN_SECRET empty for interactive setup — open the UI and click Generate.
# Set it only for headless/scripts that call /admin/* without the UI.
ADMIN_SECRET=
FARM_PORT=${FARM_PORT}
EOF
  warn "Created $ENV_FILE (ADMIN_SECRET empty — create it in the UI on first open)"
fi

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a
FARM_PORT="${FARM_PORT:-8485}"
FARM_HTTP="http://localhost:${FARM_PORT}"
ADMIN_SECRET="${ADMIN_SECRET:-}"

if [[ "$DOCKER_UI" == "false" ]]; then
  stop_vite
fi

# ---------------------------------------------------------------------------
# Build images
# ---------------------------------------------------------------------------
cd "$MCPFARM_DIR"

if [[ "$DO_BUILD" == "true" ]]; then
  info "Building auth-gateway..."
  docker compose build auth-gateway
  success "auth-gateway built"

  info "Building mcpfarm-ui..."
  docker compose build mcpfarm-ui
  success "mcpfarm-ui built"
else
  info "Skipping Docker builds (pass --build to rebuild images)"
fi

# ---------------------------------------------------------------------------
# UI upstream for Caddy
# ---------------------------------------------------------------------------
export UI_UPSTREAM="${UI_UPSTREAM:-mcpfarm-ui:3000}"

# ---------------------------------------------------------------------------
# Start infra (no Cloudflare tunnel)
# ---------------------------------------------------------------------------
wait_healthy() {
  local name="$1"
  local label="$2"
  echo -n "  Waiting for ${label}"
  for _ in $(seq 1 30); do
    if docker inspect --format '{{.State.Health.Status}}' "$name" 2>/dev/null | grep -q "healthy"; then
      echo ""
      return 0
    fi
    echo -n "."
    sleep 2
  done
  echo ""
  return 1
}

info "Starting auth-gateway (UI_UPSTREAM=${UI_UPSTREAM})..."
UI_UPSTREAM="$UI_UPSTREAM" docker compose up -d --no-deps --force-recreate auth-gateway
wait_healthy mcpfarm-auth "auth-gateway" \
  || error "auth-gateway unhealthy — check: docker logs mcpfarm-auth"
success "auth-gateway healthy"

info "Starting Caddy on port ${FARM_PORT}..."
UI_UPSTREAM="$UI_UPSTREAM" docker compose up -d --no-deps caddy
wait_healthy mcpfarm-caddy "caddy" \
  || error "Caddy unhealthy — check: docker logs mcpfarm-caddy"
success "Caddy healthy at ${FARM_HTTP}"

if [[ "$DOCKER_UI" == "true" ]]; then
  stop_vite
fi

# ---------------------------------------------------------------------------
# Seed + reload routes
# ---------------------------------------------------------------------------
info "Seeding database (idempotent)..."
docker exec mcpfarm-auth python seed.py 2>&1 | tail -3 || true

info "Starting UI container for ${FARM_HTTP}..."
docker compose up -d --no-deps mcpfarm-ui
success "mcpfarm-ui started"

reload_routes

# ---------------------------------------------------------------------------
# Optional MCP servers
# ---------------------------------------------------------------------------
start_server_list() {
  local -a list=("$@")
  [[ ${#list[@]} -eq 0 ]] && return 0
  info "Starting MCP servers: ${list[*]}"
  docker compose up -d --pull never --no-deps "${list[@]}" >/dev/null 2>&1 || \
    warn "Some servers failed to start — run: docker compose up -d --no-deps <name>-mcp"
  success "Server start requested"
}

if [[ -n "$SERVERS" ]]; then
  IFS=',' read -r -a SERVER_ARR <<< "$SERVERS"
  start_server_list "${SERVER_ARR[@]}"
elif [[ "$START_SERVERS" == "true" ]]; then
  start_server_list "${DEFAULT_SERVERS[@]}"
fi

# ---------------------------------------------------------------------------
# Health summary
# ---------------------------------------------------------------------------
HEALTH=$(curl -s "${FARM_HTTP}/health" 2>&1 || true)
[[ "$HEALTH" == "OK" ]] && success "API health → OK" || warn "API health → ${HEALTH:-unreachable}"

echo ""
echo "============================================================"
echo "  MCP Farm is running locally"
echo ""
echo "  API / backend:  ${FARM_HTTP}"
if [[ -n "${ADMIN_SECRET}" ]]; then
  echo "  Admin secret:   ${ADMIN_SECRET}"
else
  echo "  Admin secret:   (not in .env — open ${FARM_HTTP}/ and click Generate)"
fi
echo ""
if [[ "$DOCKER_UI" == "true" ]]; then
  echo "  UI:             ${FARM_HTTP}/"
  echo ""
  echo "  Stop:           ./start_mcpfarm.sh --stop"
else
  echo "  UI (built):     ${FARM_HTTP}/"
  echo "  UI (live dev):  http://localhost:${UI_DEV_PORT}/  ← file changes apply here"
  echo ""
  if [[ "$FOREGROUND" == "true" ]]; then
    echo "  Mode:           foreground (Ctrl+C stops UI only)"
  else
    echo "  Mode:           daemon (Vite PID: ${VITE_PID_FILE})"
    echo "  UI logs:        tail -f ${VITE_LOG_FILE}"
    echo "  Stop:           ./start_mcpfarm.sh --stop"
  fi
fi
echo ""
echo "  Start a server: docker compose -f mcpfarm/docker-compose.yml \\"
echo "                    up -d --no-deps nmap-mcp"
echo "============================================================"
echo ""

# ---------------------------------------------------------------------------
# UI dev server (5173 live reload; 8485 uses mcpfarm-ui container above)
# ---------------------------------------------------------------------------
if [[ "$DOCKER_UI" == "false" ]]; then
  if [[ "$FOREGROUND" == "true" ]]; then
    start_vite_foreground
  else
    start_vite_daemon
  fi
fi
