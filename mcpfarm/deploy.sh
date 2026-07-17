#!/usr/bin/env bash
# =============================================================================
# Hackerdogs MCP Server Farm — Deployment Script
# =============================================================================
# The farm is just Docker services on FARM_PORT (default 8485). Put any TLS
# proxy / tunnel / load balancer in front yourself — this script never
# configures or depends on one.
#
# Usage:
#   ./deploy.sh help
#   ./deploy.sh up [--skip-build] [--start-all]
#   ./deploy.sh down
#   ./deploy.sh start <name>-mcp ... | --all
#   ./deploy.sh stop  <name>-mcp ... | --all | --infra
#   ./deploy.sh restart <name>-mcp ... | --all | --infra
#   ./deploy.sh status
#   ./deploy.sh reload
#   ./deploy.sh seed
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERR]${NC}  $*"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
cd "$SCRIPT_DIR"

FARM_PORT="${FARM_PORT:-8485}"
FARM_HTTP="${FARM_HTTP:-http://localhost:${FARM_PORT}}"
INFRA_SERVICES=(auth-gateway caddy mcpfarm-ui)

usage() {
  cat <<EOF
Hackerdogs MCP Server Farm — deploy.sh

Usage:
  ./deploy.sh <command> [options]

Commands:
  help                 Show this help
  up                   Start farm infra (auth-gateway, caddy, ui), seed DB, load routes
  down                 Stop and remove farm containers (infra + MCP servers)
  start <svc>...       Start one or more MCP servers (e.g. naabu-mcp)
  start --all          Start all MCP servers from port-map.json (needs lots of RAM)
  stop <svc>...        Stop one or more MCP servers
  stop --all           Stop all MCP server containers
  stop --infra         Stop infra only (caddy, auth-gateway, ui)
  restart <svc>...     Restart servers (or --all / --infra)
  status               Show infra health + running MCP containers
  reload               Hot-reload Caddy routes from the auth-gateway
  seed                 Re-run database seed (registers servers from port-map.json)

up options:
  --skip-build         Do not build images (pull/use what is already local)
  --start-all          After infra is up, also start every MCP server

Environment:
  ADMIN_SECRET         Admin API password (auto-generated on first up if unset)
  FARM_PORT            Host port for Caddy (default: 8485)
  FARM_HTTP            Base URL for health/admin calls (default: http://localhost:\$FARM_PORT)
  MCPFARM_SECRETS_KEY  Fernet key for encrypted LLM provider vault (optional)

Examples:
  ADMIN_SECRET=secret ./deploy.sh up --skip-build
  ./deploy.sh start naabu-mcp nuclei-mcp
  ./deploy.sh stop --all
  ./deploy.sh status
EOF
}

need_docker() {
  command -v docker &>/dev/null || error "Docker not found."
  docker info &>/dev/null || error "Docker daemon not running."
}

need_python() {
  command -v python3 &>/dev/null || error "python3 not found."
}

load_env() {
  if [[ -f "$SCRIPT_DIR/.env" ]]; then
    # shellcheck disable=SC1091
    set -a
    # Don't export empty shell-breaking lines; simple KEY=VAL only
    while IFS= read -r line || [[ -n "$line" ]]; do
      [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
      if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
        export "$line"
      fi
    done < "$SCRIPT_DIR/.env"
    set +a
  fi
  FARM_PORT="${FARM_PORT:-8485}"
  FARM_HTTP="${FARM_HTTP:-http://localhost:${FARM_PORT}}"
}

ensure_admin_secret() {
  if [[ -z "${ADMIN_SECRET:-}" ]]; then
    ADMIN_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    warn "ADMIN_SECRET not set — generated: $ADMIN_SECRET"
    warn "Save this — it's your admin API password."
  fi
}

write_env() {
  local tmp
  tmp=$(mktemp)
  if [[ -f "$SCRIPT_DIR/.env" ]]; then
    grep -vE '^(ADMIN_SECRET|FARM_PORT)=' "$SCRIPT_DIR/.env" > "$tmp" || true
  fi
  {
    echo "ADMIN_SECRET=${ADMIN_SECRET}"
    echo "FARM_PORT=${FARM_PORT}"
    cat "$tmp"
  } > "$SCRIPT_DIR/.env"
  rm -f "$tmp"
  success ".env updated (ADMIN_SECRET, FARM_PORT)"
}

mcp_names() {
  python3 -c '
import json
with open("port-map.json") as f:
    data = json.load(f)
for name in sorted(data):
    print(name)
'
}

wait_healthy() {
  local container="$1" label="$2" tries="${3:-30}"
  echo -n "  Waiting for ${label} to be healthy"
  for _ in $(seq 1 "$tries"); do
    if docker inspect --format '{{.State.Health.Status}}' "$container" 2>/dev/null | grep -q healthy; then
      echo ""
      success "$label healthy"
      return 0
    fi
    echo -n "."
    sleep 2
  done
  echo ""
  error "$label failed to become healthy. Check: docker logs $container"
}

cmd_up() {
  local SKIP_BUILD=false START_ALL=false
  for arg in "$@"; do
    case "$arg" in
      --skip-build) SKIP_BUILD=true ;;
      --start-all)  START_ALL=true ;;
      -h|--help) usage; return 0 ;;
      *) error "Unknown up option: $arg (try ./deploy.sh help)" ;;
    esac
  done

  need_docker
  need_python
  load_env
  ensure_admin_secret
  write_env

  echo ""
  echo "============================================================"
  echo "   Hackerdogs MCP Server Farm — up"
  echo "============================================================"
  echo ""

  mkdir -p "$SCRIPT_DIR/build-logs"

  if [[ "$SKIP_BUILD" == "false" ]]; then
    info "Building auth-gateway image..."
    docker compose build auth-gateway
    success "auth-gateway built"

    info "Building mcpfarm-ui image..."
    docker compose build mcpfarm-ui
    success "mcpfarm-ui built"

    info "Building MCP server images (this takes a while)..."
    BUILT=0; FAILED=0; FAIL_LIST=()
    while IFS= read -r name; do
      dir="$REPO_DIR/$name"
      [[ -f "$dir/Dockerfile" ]] || continue
      if docker build -t "hackerdogs/${name}:latest" "$dir" \
           > "$SCRIPT_DIR/build-logs/${name}.log" 2>&1; then
        BUILT=$((BUILT + 1))
      else
        FAILED=$((FAILED + 1))
        FAIL_LIST+=("$name")
      fi
      echo -ne "\r  Built: ${BUILT}  Failed: ${FAILED}  "
    done < <(mcp_names)
    echo ""
    success "Image builds complete — $BUILT built, $FAILED failed"
    if [[ ${#FAIL_LIST[@]} -gt 0 ]]; then
      warn "Failed: ${FAIL_LIST[*]}"
      warn "Check build-logs/ for details."
    fi
  else
    info "Skipping image builds (--skip-build)"
  fi

  info "Starting infra (auth-gateway, caddy, mcpfarm-ui)..."
  docker compose up -d --no-deps auth-gateway
  wait_healthy mcpfarm-auth auth-gateway

  docker compose up -d --no-deps caddy
  wait_healthy mcpfarm-caddy caddy

  docker compose up -d --no-deps mcpfarm-ui
  success "mcpfarm-ui started"

  cmd_seed
  cmd_reload

  if [[ "$START_ALL" == "true" ]]; then
    cmd_start --all
  fi

  info "Verifying deployment..."
  HEALTH=$(curl -s "${FARM_HTTP}/health" 2>&1 || true)
  if [[ "$HEALTH" == "OK" || "$HEALTH" == *"\"status\":\"ok\""* || "$HEALTH" == *'"status": "ok"'* ]]; then
    success "${FARM_HTTP}/health → OK"
  else
    warn "Health check returned: $HEALTH"
  fi

  STATS=$(curl -s "${FARM_HTTP}/admin/stats" -H "X-Admin-Secret: ${ADMIN_SECRET}" 2>&1 || true)
  echo ""
  echo "Farm stats:"
  echo "$STATS" | python3 -m json.tool 2>/dev/null || echo "$STATS"

  echo ""
  echo "============================================================"
  echo "  Farm is up at ${FARM_HTTP}"
  echo ""
  echo "  Dashboard:  ${FARM_HTTP}/"
  echo "  Health:     ${FARM_HTTP}/health"
  echo "  Start tool: ./deploy.sh start naabu-mcp"
  echo "  Status:     ./deploy.sh status"
  echo "============================================================"
  echo ""
}

cmd_down() {
  need_docker
  info "Stopping farm (infra + MCP servers)..."
  docker compose down --remove-orphans
  success "Farm stopped"
}

cmd_start() {
  need_docker
  if [[ $# -eq 0 ]]; then
    error "Usage: ./deploy.sh start <name>-mcp ... | --all"
  fi
  if [[ "$1" == "--all" ]]; then
    info "Starting all MCP servers in batches..."
    local BATCH=() COUNT=0
    while IFS= read -r svc; do
      BATCH+=("$svc")
      if [[ ${#BATCH[@]} -ge 10 ]]; then
        docker compose up -d --pull never --no-deps "${BATCH[@]}" >/dev/null 2>&1 || true
        BATCH=()
        COUNT=$((COUNT + 10))
        echo -ne "\r  Started: ~${COUNT}  "
        sleep 2
      fi
    done < <(mcp_names)
    if [[ ${#BATCH[@]} -gt 0 ]]; then
      docker compose up -d --pull never --no-deps "${BATCH[@]}" >/dev/null 2>&1 || true
    fi
    echo ""
    success "MCP servers start requested"
    return
  fi
  info "Starting: $*"
  docker compose up -d --pull never --no-deps "$@"
  success "Started: $*"
}

cmd_stop() {
  need_docker
  if [[ $# -eq 0 ]]; then
    error "Usage: ./deploy.sh stop <name>-mcp ... | --all | --infra"
  fi
  if [[ "$1" == "--infra" ]]; then
    info "Stopping infra..."
    docker compose stop "${INFRA_SERVICES[@]}"
    success "Infra stopped"
    return
  fi
  if [[ "$1" == "--all" ]]; then
    info "Stopping all MCP servers..."
    local list=()
    while IFS= read -r svc; do list+=("$svc"); done < <(mcp_names)
    if [[ ${#list[@]} -gt 0 ]]; then
      docker compose stop "${list[@]}" >/dev/null 2>&1 || true
    fi
    success "All MCP servers stopped"
    return
  fi
  info "Stopping: $*"
  docker compose stop "$@"
  success "Stopped: $*"
}

cmd_restart() {
  need_docker
  if [[ $# -eq 0 ]]; then
    error "Usage: ./deploy.sh restart <name>-mcp ... | --all | --infra"
  fi
  if [[ "$1" == "--infra" ]]; then
    info "Restarting infra..."
    docker compose restart "${INFRA_SERVICES[@]}"
    success "Infra restarted"
    return
  fi
  if [[ "$1" == "--all" ]]; then
    info "Restarting all MCP servers..."
    local list=()
    while IFS= read -r svc; do list+=("$svc"); done < <(mcp_names)
    if [[ ${#list[@]} -gt 0 ]]; then
      docker compose restart "${list[@]}" >/dev/null 2>&1 || true
    fi
    success "All MCP servers restart requested"
    return
  fi
  info "Restarting: $*"
  docker compose restart "$@"
  success "Restarted: $*"
}

cmd_status() {
  need_docker
  load_env
  echo ""
  echo "Farm endpoint: ${FARM_HTTP}"
  echo ""
  echo "Infra:"
  docker compose ps auth-gateway caddy mcpfarm-ui 2>/dev/null || true
  echo ""
  HEALTH=$(curl -s "${FARM_HTTP}/health" 2>&1 || true)
  echo "Health: ${HEALTH}"
  echo ""
  echo "Running MCP containers:"
  docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' \
    | grep -E 'NAMES|-mcp' || echo "(none)"
  echo ""
  if [[ -n "${ADMIN_SECRET:-}" ]]; then
    echo "Admin stats:"
    curl -s "${FARM_HTTP}/admin/stats" -H "X-Admin-Secret: ${ADMIN_SECRET}" \
      | python3 -m json.tool 2>/dev/null || true
  else
    warn "ADMIN_SECRET not set — skip admin stats (set in .env or env)"
  fi
  echo ""
}

cmd_reload() {
  need_docker
  load_env
  [[ -n "${ADMIN_SECRET:-}" ]] || error "ADMIN_SECRET required (set in .env or environment)"
  info "Reloading Caddy routes..."
  local RELOAD
  RELOAD=$(curl -s -X POST "${FARM_HTTP}/admin/reload" \
    -H "X-Admin-Secret: ${ADMIN_SECRET}" 2>&1 || true)
  if echo "$RELOAD" | grep -qi 'reload\|ok\|success\|routes'; then
    success "Routes reloaded"
  else
    warn "Route reload returned: $RELOAD"
  fi
}

cmd_seed() {
  need_docker
  info "Seeding database..."
  local SEED_OUT
  SEED_OUT=$(docker exec mcpfarm-auth python seed.py 2>&1) || {
    warn "Seed failed — is auth-gateway running? ./deploy.sh up"
    echo "$SEED_OUT"
    return 1
  }
  echo "$SEED_OUT" | tail -5
  local ADMIN_KEY
  ADMIN_KEY=$(echo "$SEED_OUT" | grep "Admin API Key:" | awk '{print $NF}' || true)
  if [[ -n "${ADMIN_KEY:-}" ]]; then
    echo ""
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}  ADMIN API KEY (save this — shown only once):${NC}"
    echo -e "${GREEN}  $ADMIN_KEY${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
  else
    info "Admin key already exists (re-deploy). Not shown again."
  fi
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
CMD="${1:-}"
if [[ -z "$CMD" ]]; then
  usage
  exit 1
fi
shift || true

case "$CMD" in
  -h|--help|help) usage ;;
  up)             cmd_up "$@" ;;
  down)           cmd_down "$@" ;;
  start)          cmd_start "$@" ;;
  stop)           cmd_stop "$@" ;;
  restart)        cmd_restart "$@" ;;
  status)         cmd_status "$@" ;;
  reload)         cmd_reload "$@" ;;
  seed)           cmd_seed "$@" ;;
  # Back-compat: old flag-only invocation behaved like "up"
  --skip-build|--start-all)
    cmd_up "$CMD" "$@"
    ;;
  *)
    error "Unknown command: $CMD (try ./deploy.sh help)"
    ;;
esac
