#!/usr/bin/env bash
# ============================================================
#  CyberCom Platform API (cymed) — Production Deploy
#  Run on the OCI VM by .github/workflows/deploy-backend.yml.
#
#  Docker Compose based, mirroring the proven pattern already running
#  the rest of the platform on this VM (/opt/cybercom-platform's
#  docker-compose.production.yml). Deploys to its own isolated stack
#  at /opt/cybercom-api (port 8011, own network/volumes) rather than
#  touching the existing /opt/cybercom-platform stack that already
#  serves api.cy-com.com on 8010 — cutting real traffic over is a
#  separate, explicitly-approved step once this is verified healthy.
#
#  Release layout (see deploy-backend.yml's bundle step):
#    release_dir/cymed/          — Django project (manage.py etc.)
#    release_dir/platform/       — shared package, sibling of cymed/
#    release_dir/infrastructure/ — Dockerfile.cymed + docker-compose.api.yml
# ============================================================
set -Eeuo pipefail

release="${1:?usage: deploy-production.sh <git-sha>}"
app_root="${APP_ROOT:-/opt/cybercom-api}"
release_dir="${RELEASE_DIR:-$app_root/releases/$release}"
shared_env="$app_root/shared/.env.production"
compose="docker compose --env-file $shared_env -f docker-compose.api.yml"
port="${APP_PORT:-8011}"

if [[ ! "$release" =~ ^[0-9a-f]{7,40}$ ]]; then
  echo "Invalid release identifier: $release" >&2
  exit 2
fi

if [[ ! -r "$shared_env" ]]; then
  echo "Missing production environment file: $shared_env" >&2
  exit 3
fi

ln -sfn "$release_dir" "$app_root/current"
cd "$app_root/current"

# docker-compose.api.yml's backend/celery-worker services each have their
# own "env_file: .env.production" directive (needed so the containers get
# those vars at runtime) - that's resolved relative to THIS directory by
# Compose, completely separately from the --env-file flag below (which
# only controls ${VAR} substitution inside the compose YAML itself, not
# each service's env_file:). Without this symlink, Compose fails to load
# the project at all - even commands that only touch postgres/redis - the
# whole file is parsed up front.
ln -sfn "$shared_env" "$app_root/current/.env.production"

echo "==> Building image for release $release"
$compose build

echo "==> Starting database, cache, and identity provider"
$compose up -d postgres redis keycloak
echo "    Waiting for postgres to be ready..."
pg_ready=0
for attempt in $(seq 1 60); do
  if $compose exec -T postgres sh -c 'pg_isready -U "$POSTGRES_USER"' >/dev/null 2>&1; then
    echo "    postgres ready after ${attempt} attempt(s)"
    pg_ready=1
    break
  fi
  echo "    ...still waiting (attempt ${attempt}/60)"
  sleep 2
done
if [[ "$pg_ready" != 1 ]]; then
  echo "postgres never became ready" >&2
  echo "---- postgres logs ----" >&2
  $compose logs --tail=100 postgres >&2 || true
  exit 5
fi

echo "==> Running database migrations"
$compose run --rm backend python manage.py migrate --noinput

echo "==> Collecting static files"
$compose run --rm backend python manage.py collectstatic --noinput --clear || true

echo "==> Starting all services"
$compose up -d

echo "==> Waiting for health check on port $port"
healthy=0
for attempt in {1..30}; do
  if curl --fail --silent --show-error "http://127.0.0.1:${port}/health" >/dev/null; then
    echo "Release $release is healthy and active on port $port"
    healthy=1
    break
  fi
  if [[ "$attempt" == 30 ]]; then
    echo "Health check failed for release $release" >&2
    echo "---- backend logs ----" >&2
    $compose logs --tail=100 backend >&2 || true
    exit 4
  fi
  sleep 2
done

# Idempotent — safe to run on every deploy. Creates the shared "cybercom"
# realm/client/admin-user on first run, no-ops (just rotates the admin
# password) on later runs. Output goes to a file on the server, NOT
# workflow stdout — it prints a real client secret + admin password in
# cleartext, and workflow logs are not the place for that. Read it via
# SSH: cat /opt/cybercom-api/shared/keycloak-bootstrap-output.txt
if [[ "$healthy" == 1 ]]; then
  echo "==> Bootstrapping shared Keycloak realm (output not shown here — see $app_root/shared/keycloak-bootstrap-output.txt on the server)"
  admin_email="${PLATFORM_ADMIN_EMAIL:-admin@cy-com.com}"
  $compose run --rm backend python manage.py bootstrap_platform_realm --admin-email "$admin_email" \
    > "$app_root/shared/keycloak-bootstrap-output.txt" 2>&1 || {
      echo "Keycloak bootstrap step failed — check $app_root/shared/keycloak-bootstrap-output.txt on the server" >&2
    }
fi
