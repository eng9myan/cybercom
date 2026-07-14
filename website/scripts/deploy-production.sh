#!/usr/bin/env bash
set -Eeuo pipefail

release="${1:?usage: deploy-production.sh <git-sha>}"
app_root="${APP_ROOT:-/opt/cybercom-website}"
release_dir="${RELEASE_DIR:-$app_root/releases/$release}"
shared_env="$app_root/shared/.env.production"
compose_file="$release_dir/docker-compose.production.yml"

if [[ ! "$release" =~ ^[0-9a-f]{7,40}$ ]]; then
  echo "Invalid release identifier: $release" >&2
  exit 2
fi

if [[ ! -r "$shared_env" ]]; then
  echo "Missing production environment file: $shared_env" >&2
  exit 3
fi

previous=""
if [[ -r "$app_root/current-release" ]]; then
  previous="$(<"$app_root/current-release")"
fi

ln -sfn "$shared_env" "$release_dir/.env.production"

echo "Building CyberCom release $release"
DOCKER_BUILDKIT=1 docker build \
  --secret "id=production_env,src=$shared_env" \
  --label "com.cybercom.release=$release" \
  --tag "cybercom-website:$release" \
  "$release_dir"

rollback_on_error() {
  status=$?
  if [[ -n "$previous" ]] && docker image inspect "cybercom-website:$previous" >/dev/null 2>&1; then
    echo "Deployment failed; restoring $previous" >&2
    CYBERCOM_RELEASE="$previous" docker compose -f "$app_root/releases/$previous/docker-compose.production.yml" up -d --no-build
  fi
  exit "$status"
}
trap rollback_on_error ERR

existing_project="$(docker inspect --format '{{ index .Config.Labels "com.docker.compose.project" }}' cybercom-website 2>/dev/null || true)"
if [[ -n "$existing_project" && "$existing_project" != "cybercom-website" ]]; then
  echo "Migrating container from legacy Compose project $existing_project"
  docker rm --force cybercom-website
fi

CYBERCOM_RELEASE="$release" docker compose -f "$compose_file" up -d --no-build

for attempt in {1..30}; do
  if curl --fail --silent --show-error http://127.0.0.1:3000/api/health >/dev/null; then
    break
  fi
  if [[ "$attempt" == 30 ]]; then
    echo "Health check failed for release $release" >&2
    exit 4
  fi
  sleep 2
done

"$release_dir/scripts/configure-nginx.sh"

if [[ -n "$previous" && "$previous" != "$release" ]]; then
  printf '%s\n' "$previous" > "$app_root/previous-release"
fi
printf '%s\n' "$release" > "$app_root/current-release"

trap - ERR
echo "Release $release is healthy and active"
