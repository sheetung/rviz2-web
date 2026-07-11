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
  if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
    log "Loaded $ENV_FILE"
  fi
}

load_ros() {
  set +u
  [[ -f /opt/ros/humble/setup.bash ]] && source /opt/ros/humble/setup.bash
  [[ -f /home/amov/super_ros2_ws/install/setup.bash ]] && source /home/amov/super_ros2_ws/install/setup.bash
  set -u
}

check_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing command: $1"
}

check_port() {
  local port="$1"
  if ss -ltn "sport = :$port" 2>/dev/null | grep -q LISTEN; then
    fail "Port $port is already in use"
  fi
}

wait_for_http() {
  local url="$1" name="$2" pid="$3"
  for _ in {1..50}; do
    kill -0 "$pid" 2>/dev/null || fail "$name exited during startup; see $LOG_DIR"
    curl -fsS "$url" >/dev/null 2>&1 && return 0
    sleep 0.2
  done
  fail "$name did not become ready: $url"
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
  check_command uv
  check_command npm
  check_command curl
  check_command ss
  check_command setsid
  load_env
  load_ros

  local backend_port="${WEB_PORT:-8000}"
  local frontend_port="${FRONTEND_PORT:-3000}"
  check_port "$backend_port"
  check_port "$frontend_port"

  [[ -d "$BACKEND_DIR/.venv" ]] || fail "Backend environment missing. Run: cd backend && uv sync"
  [[ -d "$FRONTEND_DIR/node_modules" ]] || fail "Frontend dependencies missing. Run: cd frontend && npm ci"
  "$BACKEND_DIR/.venv/bin/python" -c "import rclpy" || fail "rclpy is unavailable; check the ROS2 setup files"

  trap cleanup INT TERM EXIT

  log "Starting backend on $backend_port"
  (
    cd "$BACKEND_DIR"
    exec setsid uv run --no-sync uvicorn app.main:app --host "${WEB_HOST:-0.0.0.0}" --port "$backend_port"
  ) >"$LOG_DIR/backend.log" 2>&1 &
  BACKEND_PID=$!
  wait_for_http "http://127.0.0.1:$backend_port/health" backend "$BACKEND_PID"

  log "Starting frontend on $frontend_port"
  (
    cd "$FRONTEND_DIR"
    exec setsid npm run dev -- --host "${FRONTEND_HOST:-0.0.0.0}" --port "$frontend_port"
  ) >"$LOG_DIR/frontend.log" 2>&1 &
  FRONTEND_PID=$!
  wait_for_http "http://127.0.0.1:$frontend_port" frontend "$FRONTEND_PID"

  log "Frontend: http://192.168.1.66:$frontend_port"
  log "Backend:  http://127.0.0.1:$backend_port"
  wait -n "$BACKEND_PID" "$FRONTEND_PID"
  fail "A service stopped unexpectedly; see $LOG_DIR"
}

show_help() {
  printf 'Usage: %s [local|sync|help]\n' "$0"
  printf '  sync   Install/update backend and frontend dependencies\n'
  printf '  local  Start both services (default)\n'
}

case "${1:-local}" in
  sync)
    check_command uv
    check_command npm
    (
      cd "$BACKEND_DIR"
      [[ -d .venv ]] || uv venv --system-site-packages .venv
      VIRTUAL_ENV="$BACKEND_DIR/.venv" uv sync --active
    )
    (cd "$FRONTEND_DIR" && npm ci)
    ;;
  local) start_local ;;
  help|-h|--help) show_help ;;
  *) show_help; exit 2 ;;
esac
