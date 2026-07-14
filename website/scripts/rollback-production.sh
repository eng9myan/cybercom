#!/usr/bin/env bash
set -Eeuo pipefail

app_root="${APP_ROOT:-/opt/cybercom-website}"
target="${1:-}"

if [[ -z "$target" && -r "$app_root/previous-release" ]]; then
  target="$(<"$app_root/previous-release")"
fi

if [[ ! "$target" =~ ^[0-9a-f]{7,40}$ ]]; then
  echo "Usage: rollback-production.sh [git-sha]" >&2
  exit 2
fi

release_dir="$app_root/releases/$target"
if [[ ! -f "$release_dir/docker-compose.production.yml" ]]; then
  echo "Release files not found: $release_dir" >&2
  exit 3
fi
if ! docker image inspect "cybercom-website:$target" >/dev/null 2>&1; then
  echo "Docker image not found: cybercom-website:$target" >&2
  exit 4
fi

current=""
if [[ -r "$app_root/current-release" ]]; then
  current="$(<"$app_root/current-release")"
fi

CYBERCOM_RELEASE="$target" docker compose -f "$release_dir/docker-compose.production.yml" up -d --no-build
curl --fail --retry 20 --retry-delay 2 --retry-connrefused http://127.0.0.1:3000/api/health >/dev/null

if [[ -n "$current" && "$current" != "$target" ]]; then
  printf '%s\n' "$current" > "$app_root/previous-release"
fi
printf '%s\n' "$target" > "$app_root/current-release"
echo "Rolled back to $target"
