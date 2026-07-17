#!/usr/bin/env bash
set -Eeuo pipefail

export PATH="$HOME/.local/bin:$PATH"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
ENV_FILE="$PROJECT_ROOT/.env"

log() { printf '[rvizweb] %s\n' "$*"; }
fail() { printf '[rvizweb] ERROR: %s\n' "$*" >&2; exit 1; }

check_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing command: $1"
}

ensure_env() {
  [[ -f "$ENV_FILE" ]] && return

  local env_example="$PROJECT_ROOT/.env.example"
  [[ -f "$env_example" ]] || fail "Missing environment template: $env_example"
  cp "$env_example" "$ENV_FILE"
  log "Created $ENV_FILE from $env_example"
}

load_env() {
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
}

load_ros() {
  set +u
  local setup_file
  for setup_file in ${ROS2_SETUP_PATHS:-}; do
    [[ -f "$setup_file" ]] && source "$setup_file"
  done
  set -u
}

ensure_uv() {
  command -v uv >/dev/null 2>&1 && return

  check_command curl
  log "uv not found; installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  hash -r
  command -v uv >/dev/null 2>&1 || fail "uv installation completed but uv is not available in PATH"
}

run_as_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
    return
  fi

  check_command sudo
  sudo "$@"
}

ensure_ffmpeg() {
  local ffmpeg_command="${FFMPEG_PATH:-ffmpeg}"
  command -v "$ffmpeg_command" >/dev/null 2>&1 && return

  if [[ "$ffmpeg_command" != "ffmpeg" ]]; then
    fail "Configured FFMPEG_PATH is not executable or not in PATH: $ffmpeg_command"
  fi

  log "ffmpeg not found; installing ffmpeg"
  if command -v apt-get >/dev/null 2>&1; then
    run_as_root apt-get update
    run_as_root apt-get install -y ffmpeg
  elif command -v dnf >/dev/null 2>&1; then
    run_as_root dnf install -y ffmpeg
  elif command -v yum >/dev/null 2>&1; then
    run_as_root yum install -y ffmpeg
  elif command -v pacman >/dev/null 2>&1; then
    run_as_root pacman -Sy --noconfirm ffmpeg
  else
    fail "ffmpeg is missing and no supported package manager was found; install ffmpeg manually"
  fi

  hash -r
  command -v ffmpeg >/dev/null 2>&1 || fail "ffmpeg installation completed but ffmpeg is not available in PATH"
}

install_dependencies() {
  log "Installing/updating backend dependencies"
  (
    cd "$BACKEND_DIR"
    [[ -d .venv ]] || uv venv --system-site-packages .venv
    VIRTUAL_ENV="$BACKEND_DIR/.venv" uv sync --active
  )

  log "Installing/updating frontend dependencies"
  (cd "$FRONTEND_DIR" && npm ci)
}

main() {
  ensure_env
  load_env
  load_ros
  ensure_uv
  check_command npm
  check_command ss
  check_command setsid
  ensure_ffmpeg
  install_dependencies
  log "Installation complete"
}

main "$@"
