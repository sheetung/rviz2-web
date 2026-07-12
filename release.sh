#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION=""
RELEASE_NOTE="维护版本发布。"
PUSH_RELEASE=0
GENERATED=0

log() { printf '[release] %s\n' "$*"; }
fail() { printf '[release] ERROR: %s\n' "$*" >&2; exit 1; }

load_project_environment() {
  if [[ -f "$PROJECT_ROOT/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env"
    set +a
  fi

  set +u
  local setup_file
  for setup_file in ${ROS2_SETUP_PATHS:-}; do
    [[ -f "$setup_file" ]] && source "$setup_file"
  done
  set -u
}

show_help() {
  printf '用法: %s <版本号> [--note "发布说明"] [--push]\n' "$0"
  printf '示例: %s 1.0.1 --note "修复点云显示问题"\n' "$0"
  printf '      %s 1.1.0 --note "增加新功能" --push\n' "$0"
  printf '默认完成检查、测试、构建、提交和标签；--push 会继续推送当前分支和标签。\n'
}

restore_generated_files() {
  local exit_code=$?
  trap - ERR
  if [[ "$GENERATED" -eq 1 ]]; then
    log "发布失败，正在撤销脚本生成的版本改动"
    git -C "$PROJECT_ROOT" restore -- \
      VERSION CHANGELOG.md README.md README_en.md PROJECT_STATUS.md \
      frontend/package.json frontend/package-lock.json \
      backend/pyproject.toml backend/uv.lock
  fi
  exit "$exit_code"
}

parse_args() {
  [[ $# -gt 0 ]] || { show_help; exit 2; }
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --help|-h) show_help; exit 0 ;;
      --push) PUSH_RELEASE=1; shift ;;
      --note)
        [[ $# -ge 2 ]] || fail "--note 后缺少发布说明"
        RELEASE_NOTE="$2"
        shift 2
        ;;
      *)
        [[ -z "$VERSION" ]] || fail "无法识别的参数: $1"
        VERSION="$1"
        shift
        ;;
    esac
  done
}

main() {
  parse_args "$@"
  [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$ ]] || fail "版本号必须符合语义化版本，例如 1.0.1"

  cd "$PROJECT_ROOT"
  for command_name in git node npm; do
    command -v "$command_name" >/dev/null 2>&1 || fail "缺少命令: $command_name"
  done
  [[ -x backend/.venv/bin/python ]] || fail "后端环境不存在，请先运行 ./start.sh sync"
  [[ -z "$(git status --porcelain)" ]] || fail "工作区存在未提交修改，请先提交或清理"
  git rev-parse "v$VERSION" >/dev/null 2>&1 && fail "标签 v$VERSION 已存在"

  trap restore_generated_files ERR
  GENERATED=1
  log "准备 RVizWeb v$VERSION"
  node scripts/sync-version.mjs "$VERSION"
  node scripts/add-release-notes.mjs "$VERSION" "$RELEASE_NOTE"
  node scripts/sync-version.mjs --check

  log "运行前端测试与构建"
  npm --prefix frontend test
  npm --prefix frontend run lint:check
  npm --prefix frontend run build

  log "运行后端测试"
  load_project_environment
  backend/.venv/bin/python -m pytest -q backend/tests
  backend/.venv/bin/python -m compileall -q backend/app

  git add VERSION CHANGELOG.md README.md README_en.md PROJECT_STATUS.md \
    frontend/package.json frontend/package-lock.json \
    backend/pyproject.toml backend/uv.lock
  git commit -m "Release RVizWeb v$VERSION"
  git tag -a "v$VERSION" -m "RVizWeb-v$VERSION"
  GENERATED=0
  trap - ERR

  if [[ "$PUSH_RELEASE" -eq 1 ]]; then
    local branch
    branch="$(git branch --show-current)"
    [[ -n "$branch" ]] || fail "当前处于 detached HEAD，无法自动推送"
    git push origin "$branch"
    git push origin "v$VERSION"
    log "已推送分支 $branch 和标签 v$VERSION"
  else
    log "v$VERSION 已创建。确认后可执行: git push origin $(git branch --show-current) && git push origin v$VERSION"
  fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
