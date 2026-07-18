#!/usr/bin/env bash
# ============================================================
#  CyberCom Platform API Backend (cymed) — Production Deploy
#  Run on the OCI VM by .github/workflows/deploy-backend.yml.
#
#  ASSUMPTIONS — not verified against the real server, since no
#  SSH access was available while writing this. A running
#  instance already answers /health and /api/v1/identity/healthz/
#  on port 8010, so *something* is already deployed there; this
#  script assumes it's this same codebase reachable at
#  APP_ROOT below, managed by systemd (falling back to pm2 if
#  no systemd unit exists). If the first real run fails at the
#  restart step, that's the thing to fix by hand once, then this
#  script should keep working for every deploy after.
#
#  Release layout (see deploy-backend.yml's bundle step):
#    release_dir/cymed/     — this Django project (manage.py etc.)
#    release_dir/platform/  — shared package cymed imports from;
#                              must stay a SIBLING of cymed/, not
#                              nested inside it — cymed/manage.py's
#                              namespace-bridging trick resolves
#                              repo_root as its own parent directory.
# ============================================================
set -Eeuo pipefail

release="${1:?usage: deploy-production.sh <git-sha>}"
app_root="${APP_ROOT:-/opt/cybercom-api}"
release_dir="${RELEASE_DIR:-$app_root/releases/$release}"
app_dir="$release_dir/cymed"
shared_env="$app_root/shared/.env.production"
venv="$app_root/shared/venv"
service_name="${SERVICE_NAME:-cybercom-api}"
port="${APP_PORT:-8010}"

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

ln -sfn "$shared_env" "$app_dir/.env.production"

if [[ ! -d "$venv" ]]; then
  echo "Creating shared virtualenv at $venv"
  python3 -m venv "$venv"
fi

echo "Installing dependencies for release $release"
"$venv/bin/pip" install --quiet --upgrade pip
"$venv/bin/pip" install --quiet -r "$app_dir/requirements.txt"

echo "Running migrations"
( set -a; source "$shared_env"; set +a
  cd "$app_dir" && "$venv/bin/python" manage.py migrate --noinput )

echo "Collecting static files (non-fatal if unconfigured)"
( set -a; source "$shared_env"; set +a
  cd "$app_dir" && "$venv/bin/python" manage.py collectstatic --noinput ) || true

rollback_on_error() {
  status=$?
  if [[ -n "$previous" && -d "$app_root/releases/$previous" ]]; then
    echo "Deployment failed; restoring $previous" >&2
    ln -sfn "$app_root/releases/$previous" "$app_root/current"
    restart_service
  fi
  exit "$status"
}
trap rollback_on_error ERR

restart_service() {
  if systemctl list-unit-files "${service_name}.service" &>/dev/null; then
    sudo systemctl restart "$service_name"
  else
    pm2 restart "$service_name" 2>/dev/null || \
      pm2 start "$venv/bin/gunicorn" --name "$service_name" -- \
        core.wsgi:application --chdir "$app_root/current/cymed" --bind "127.0.0.1:$port" --workers 3
  fi
}

ln -sfn "$release_dir" "$app_root/current"
restart_service

echo "Waiting for health check on port $port"
for attempt in {1..30}; do
  if curl --fail --silent --show-error "http://127.0.0.1:${port}/health" >/dev/null; then
    break
  fi
  if [[ "$attempt" == 30 ]]; then
    echo "Health check failed for release $release" >&2
    exit 4
  fi
  sleep 2
done

if [[ -n "$previous" && "$previous" != "$release" ]]; then
  printf '%s\n' "$previous" > "$app_root/previous-release"
fi
printf '%s\n' "$release" > "$app_root/current-release"

trap - ERR
echo "Release $release is healthy and active on port $port"
