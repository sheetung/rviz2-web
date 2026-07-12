#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="${1:-}"

if [[ "$VERSION" == "--help" || "$VERSION" == "-h" ]]; then
  printf '用法: %s <版本号>\n示例: %s 1.0.1\n' "$0" "$0"
  exit 0
fi

[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$ ]] || {
  printf '版本号格式错误，示例: %s 1.0.1\n' "$0" >&2
  exit 2
}

cd "$ROOT"
[[ -z "$(git status --porcelain)" ]] || {
  printf '工作区存在未提交修改，请先处理。\n' >&2
  exit 1
}
git rev-parse "v$VERSION" >/dev/null 2>&1 && {
  printf '标签 v%s 已存在。\n' "$VERSION" >&2
  exit 1
}

printf '[release] 同步版本 v%s\n' "$VERSION"
node scripts/sync-version.mjs "$VERSION"
node scripts/sync-version.mjs --check

printf '[release] 运行检查\n'
npm --prefix frontend test
npm --prefix frontend run build

set +u
[[ -f .env ]] && source .env
for setup_file in ${ROS2_SETUP_PATHS:-}; do
  [[ -f "$setup_file" ]] && source "$setup_file"
done
set -u
(cd backend && .venv/bin/python -m pytest -q)

git add VERSION README.md README_en.md PROJECT_STATUS.md \
  frontend/package.json frontend/package-lock.json \
  backend/pyproject.toml backend/uv.lock
git commit -m "Release RVizWeb v$VERSION"
git tag -a "v$VERSION" -m "RVizWeb-v$VERSION"

printf '[release] 已创建 v%s\n' "$VERSION"
