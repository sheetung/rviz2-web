#!/usr/bin/env bash
set -Eeuo pipefail

export PATH="$HOME/.local/bin:$PATH"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOG_DIR="$PROJECT_ROOT/logs"
ENV_FILE="$PROJECT_ROOT/.env"
BACKEND_PID=""
FRONTEND_PID=""

mkdir -p "$LOG_DIR"

log() { printf '[rvizweb] %s\n' "$*"; }
fail() { printf '[rvizweb] ERROR: %s\n' "$*" >&2; exit 1; }

load_env() {
  [[ -f "$ENV_FILE" ]] || return

  local line key value first last
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" || "$line" == \#* ]] && continue
    [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] || fail "Invalid .env entry: $line"
    key="${line%%=*}"
    value="${line#*=}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    first="${value:0:1}"
    last="${value: -1}"
    if [[ "$first" == "'" || "$first" == '"' ]]; then
      [[ "$last" == "$first" ]] || fail "Unterminated quote for $key in $ENV_FILE"
      value="${value:1:${#value}-2}"
    fi
    export "$key=$value"
  done < "$ENV_FILE"
  log "Loaded $ENV_FILE"
}

load_ros() {
  set +u
  local setup_file
  for setup_file in ${ROS2_SETUP_PATHS:-}; do
    [[ -f "$setup_file" ]] && source "$setup_file"
  done
  set -u
}

check_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing command: $1"
}

is_initialized() {
  (
    [[ -f "$ENV_FILE" ]] || exit 1
    command -v uv >/dev/null 2>&1 || exit 1
    command -v npm >/dev/null 2>&1 || exit 1
    command -v "${FFMPEG_PATH:-ffmpeg}" >/dev/null 2>&1 || exit 1
    [[ -x "$BACKEND_DIR/.venv/bin/python" ]] || exit 1
    [[ -d "$FRONTEND_DIR/node_modules" ]] || exit 1
  )
}

ensure_initialized() {
  is_initialized && return

  local install_script="$PROJECT_ROOT/install.sh"
  [[ -x "$install_script" ]] || fail "Installation script is missing or not executable: $install_script"
  log "Project is not initialized; running install.sh"
  "$install_script"
  hash -r
  is_initialized || fail "Installation completed but the project is still not initialized"
}

check_port() {
  local port="$1"
  if ss -ltn "sport = :$port" 2>/dev/null | grep -q LISTEN; then
    fail "Port $port is already in use"
  fi
}

wait_for_http() {
  local url="$1" name="$2" pid="$3" timeout_seconds="${4:-60}"
  local max_attempts=$(( timeout_seconds * 5 ))

  for ((attempt=1; attempt<=max_attempts; attempt++)); do
    kill -0 "$pid" 2>/dev/null || fail "$name exited during startup; see $LOG_DIR"
    # Health checks target loopback services and must never be routed through
    # HTTP_PROXY/HTTPS_PROXY inherited from the user's shell.
    curl --noproxy '*' -fsS "$url" >/dev/null 2>&1 && return 0

    if (( attempt % 20 == 0 )); then
      log "Still waiting for $name at $url ($attempt/$max_attempts)"
    fi

    sleep 0.2
  done

  fail "$name did not become ready within ${timeout_seconds}s: $url"
}

health_host_for_bind() {
  case "$1" in
    0.0.0.0) printf '127.0.0.1' ;;
    "::"|"::1") printf '[::1]' ;;
    *) printf '%s' "$1" ;;
  esac
}

cleanup() {
  trap - INT TERM EXIT
  log "Stopping services"
  for pid in "$FRONTEND_PID" "$BACKEND_PID"; do
    [[ -n "$pid" ]] || continue
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
  done
  for _ in {1..30}; do
    local alive=0
    for pid in "$FRONTEND_PID" "$BACKEND_PID"; do
      [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null && alive=1
    done
    [[ "$alive" -eq 0 ]] && return
    sleep 0.1
  done
  for pid in "$FRONTEND_PID" "$BACKEND_PID"; do
    [[ -n "$pid" ]] && kill -KILL -- "-$pid" 2>/dev/null || true
  done
}

start_local() {
  local frontend_mode="${1:-local}"
  ensure_initialized
  check_command curl
  check_command uv
  check_command npm
  check_command ss
  check_command setsid
  load_env
  load_ros

  check_command "${FFMPEG_PATH:-ffmpeg}"

  local backend_port="${BACKEND_PORT:?Set BACKEND_PORT in $ENV_FILE}"
  local frontend_port="${FRONTEND_PORT:?Set FRONTEND_PORT in $ENV_FILE}"
  local backend_host="${BACKEND_HOST:-127.0.0.1}"
  local frontend_host="${FRONTEND_HOST:-127.0.0.1}"
  local frontend_public_host="${FRONTEND_PUBLIC_HOST:-127.0.0.1}"
  local backend_health_host
  local frontend_health_host
  local allow_unauthenticated_lan="${ALLOW_UNAUTHENTICATED_LAN:-true}"
  local default_rvizweb_config="${RVIZWEB_CONFIG:?Set RVIZWEB_CONFIG in $ENV_FILE}"
  backend_health_host="$(health_host_for_bind "$backend_host")"
  frontend_health_host="$(health_host_for_bind "$frontend_host")"
  check_port "$backend_port"
  check_port "$frontend_port"

  if [[ "$backend_host" != "127.0.0.1" && "$backend_host" != "::1" && "$backend_host" != "localhost" && -z "${API_ACCESS_TOKEN:-}" && "${allow_unauthenticated_lan,,}" != "true" ]]; then
    fail "API_ACCESS_TOKEN or ALLOW_UNAUTHENTICATED_LAN=true is required when BACKEND_HOST is not loopback"
  fi
  if [[ "$frontend_host" != "127.0.0.1" && "$frontend_host" != "::1" && "$frontend_host" != "localhost" && -z "${API_ACCESS_TOKEN:-}" && "${allow_unauthenticated_lan,,}" != "true" ]]; then
    fail "API_ACCESS_TOKEN or ALLOW_UNAUTHENTICATED_LAN=true is required when FRONTEND_HOST is not loopback"
  fi
  if [[ -n "${API_ACCESS_TOKEN:-}" && "${#API_ACCESS_TOKEN}" -lt 32 ]]; then
    fail "API_ACCESS_TOKEN must contain at least 32 characters"
  fi

  [[ "$default_rvizweb_config" == *.rvizweb ]] || fail "Default frontend config must use the .rvizweb suffix"
  [[ -f "$PROJECT_ROOT/rvizweb_configs/$default_rvizweb_config" ]] || fail "Default frontend config not found: rvizweb_configs/$default_rvizweb_config"
  "$BACKEND_DIR/.venv/bin/python" -c "import rclpy" || fail "rclpy is unavailable; check the ROS2 setup files"

  if [[ "$frontend_mode" == "local" ]]; then
    log "Building frontend for normal local use"
    (
      cd "$FRONTEND_DIR"
      VITE_RVIZWEB_CONFIG="$default_rvizweb_config" npm run build
    ) >"$LOG_DIR/frontend.log" 2>&1 || fail "Frontend build failed; see $LOG_DIR/frontend.log"
  fi

  trap cleanup INT TERM EXIT

  log "Starting backend on $backend_port"
  (
    cd "$BACKEND_DIR"
    exec setsid uv run --no-sync uvicorn app.main:app --host "$backend_host" --port "$backend_port"
  ) >"$LOG_DIR/backend.log" 2>&1 &
  BACKEND_PID=$!

  log "Starting frontend on $frontend_port ($frontend_mode mode)"
  (
    cd "$FRONTEND_DIR"
    if [[ "$frontend_mode" == "dev" ]]; then
      export VITE_RVIZWEB_CONFIG="$default_rvizweb_config"
      export CHOKIDAR_USEPOLLING="${CHOKIDAR_USEPOLLING:-true}"
      export CHOKIDAR_INTERVAL="${CHOKIDAR_INTERVAL:-500}"
      exec setsid npm run dev -- --host "$frontend_host" --port "$frontend_port"
    fi
    exec setsid npm run preview -- --host "$frontend_host" --port "$frontend_port"
  ) >>"$LOG_DIR/frontend.log" 2>&1 &
  FRONTEND_PID=$!

  wait_for_http "http://$backend_health_host:$backend_port/health" backend "$BACKEND_PID" 120
  wait_for_http "http://$frontend_health_host:$frontend_port" frontend "$FRONTEND_PID" 120

  log "Frontend: http://$frontend_public_host:$frontend_port"
  log "Backend:  http://$backend_health_host:$backend_port"
  log "Config:   rvizweb_configs/$default_rvizweb_config"
  wait -n "$BACKEND_PID" "$FRONTEND_PID"
  fail "A service stopped unexpectedly; see $LOG_DIR"
}

show_help() {
  printf 'Usage: %s [local|dev|install|sync|help]\n' "$0"
  printf '  install  Install/update system, backend, and frontend dependencies\n'
  printf '  sync     Alias for install\n'
  printf '  local  Build and start for normal local use (default)\n'
  printf '  dev    Start with Vite hot reload for development\n'
}

main() {
  case "${1:-local}" in
    install|sync) "$PROJECT_ROOT/install.sh" ;;
    local) start_local local ;;
    dev) start_local dev ;;
    help|-h|--help) show_help ;;
    *) show_help; return 2 ;;
  esac
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
