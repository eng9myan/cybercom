#!/usr/bin/env bash
# ============================================================
#  Staging-clone-from-prod — Phase 4 (Odoo.sh-equivalent hosting), item 1.
#
#  Spins up (or refreshes) an isolated staging stack for one app, seeded
#  from a real pg_dump of that app's live production database. Runs on
#  the same VM as production (same pattern as deploy-production.sh: a
#  separate, isolated Compose project — own network, own volumes, own
#  port — never touches the running prod containers except to read from
#  them with pg_dump, which takes no lock that blocks writers).
#
#  Usage (on the production VM, as the deploy user):
#    clone-staging-from-prod.sh <cymed|cycom>
#
#  What it does, in order:
#    1. pg_dump the prod database (custom format) to a timestamped
#       snapshot under $app_root/snapshots/ — read-only against prod.
#    2. Bring up a *_staging Compose project's postgres (+ redis, if the
#       app has one) using the SAME compose file as prod plus a small
#       port-remapping override (docker-compose.staging.<app>.override.yml),
#       so the only thing that differs from prod is isolation + port.
#    3. Drop and recreate the staging database, then pg_restore the
#       snapshot into it. This step only ever targets the *_staging
#       Compose project — the script refuses to run if that project
#       name doesn't contain "staging" (belt-and-braces against a
#       copy-paste pointing a DROP DATABASE at the wrong stack).
#    4. For cymed: run `manage.py scrub_staging_phi --yes-this-is-staging`
#       inside the staging backend container — a real Django management
#       command, not raw SQL, because several PHI columns carry a
#       deterministic blind-index companion column that only the model
#       field's own `.save()` maintains correctly (see that command's own
#       docstring). cycom has no such command (retail ERP data, no PHI) —
#       skipped, not an error.
#    5. Bring up the rest of the staging stack (backend, celery, keycloak)
#       and print the URL to smoke-test it on.
#
#  Does NOT touch DNS, TLS or the reverse proxy — exposing the staging
#  port publicly (a staging.<app>.cy-com.com Caddy entry) is a separate,
#  explicit step once this is proven working, same "verify before cutting
#  over" discipline as deploy-production.sh.
# ============================================================
set -Eeuo pipefail

app="${1:?usage: clone-staging-from-prod.sh <cymed|cycom>}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$app" in
  cymed)
    app_root="${APP_ROOT:-/opt/cybercom-api}"
    compose_file="docker-compose.api.yml"
    postgres_service="postgres"      # cymed's compose service key
    staging_port="${STAGING_PORT:-8111}"
    override_file="docker-compose.staging.cymed.override.yml"
    ;;
  cycom)
    app_root="${APP_ROOT:-/opt/cycom-api}"
    compose_file="docker-compose.cycom-api.yml"
    postgres_service="cycom-postgres"  # cycom's compose service key differs from cymed's
    staging_port="${STAGING_PORT:-8112}"
    override_file="docker-compose.staging.cycom.override.yml"
    ;;
  *)
    echo "Unknown app '$app' — expected cymed or cycom." >&2
    exit 2
    ;;
esac

project_staging="${app}-staging"
current_dir="$app_root/current"
snapshot_dir="$app_root/snapshots"
env_staging="$app_root/shared/.env.staging"

# Belt-and-braces: the destructive drop/recreate below only ever runs
# against a Compose project whose name contains "staging" — checked once,
# up front, before anything else happens.
if [[ "$project_staging" != *staging* ]]; then
  echo "Refusing: compose project '$project_staging' does not look like a staging project." >&2
  exit 5
fi

if [[ ! -d "$current_dir" ]]; then
  echo "No release at $current_dir — deploy production at least once before cloning staging from it." >&2
  exit 3
fi

mkdir -p "$snapshot_dir"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
snapshot="$snapshot_dir/${app}-${timestamp}.dump"

compose_prod() { docker compose --env-file "$app_root/shared/.env.production" -f "$current_dir/$compose_file" "$@"; }
compose_staging() {
  docker compose -p "$project_staging" --env-file "$env_staging" \
    -f "$current_dir/$compose_file" -f "$script_dir/$override_file" "$@"
}

echo "==> [1/6] Dumping production database ($postgres_service)"
# -Fc (custom format): the only format pg_restore --clean/--if-exists needs
# for a clean reload; also compressed, matters once PHI tables grow.
prod_db="$(compose_prod exec -T "$postgres_service" sh -c 'echo "$POSTGRES_DB"')"
prod_user="$(compose_prod exec -T "$postgres_service" sh -c 'echo "$POSTGRES_USER"')"
compose_prod exec -T "$postgres_service" sh -c "pg_dump -U '$prod_user' -Fc '$prod_db'" > "$snapshot"
echo "    snapshot: $snapshot ($(du -h "$snapshot" | cut -f1))"

echo "==> [2/6] Preparing staging .env (derived from production's, own DB name/port)"
if [[ ! -r "$env_staging" ]]; then
  sed -E "s/^POSTGRES_DB=.*/POSTGRES_DB=${prod_db}_staging/" "$app_root/shared/.env.production" > "$env_staging"
  chmod 600 "$env_staging"
fi
grep -q '^APP_STAGING_PORT=' "$env_staging" || echo "APP_STAGING_PORT=${staging_port}" >> "$env_staging"

echo "==> [3/6] Bringing up the staging $postgres_service (isolated project: $project_staging)"
compose_staging up -d "$postgres_service"
for attempt in $(seq 1 30); do
  compose_staging exec -T "$postgres_service" sh -c 'pg_isready -U "$POSTGRES_USER"' >/dev/null 2>&1 && break
  sleep 2
  [[ "$attempt" -eq 30 ]] && { echo "staging $postgres_service never became ready" >&2; exit 4; }
done

echo "==> [4/6] Restoring the snapshot into staging"
staging_db="$(compose_staging exec -T "$postgres_service" sh -c 'echo "$POSTGRES_DB"')"
staging_user="$(compose_staging exec -T "$postgres_service" sh -c 'echo "$POSTGRES_USER"')"
compose_staging exec -T "$postgres_service" sh -c "dropdb -U '$staging_user' --if-exists '$staging_db'"
compose_staging exec -T "$postgres_service" sh -c "createdb -U '$staging_user' '$staging_db'"
docker cp "$snapshot" "$(compose_staging ps -q "$postgres_service"):/tmp/restore.dump"
compose_staging exec -T "$postgres_service" sh -c "pg_restore -U '$staging_user' -d '$staging_db' --no-owner --no-privileges /tmp/restore.dump" || {
  echo "pg_restore reported errors above — pg_restore's own exit code is noisy by design (missing-role warnings etc.); inspect before trusting staging." >&2
}

echo "==> [5/6] Starting the rest of the staging stack"
compose_staging up -d

if [[ "$app" == "cymed" ]]; then
  echo "==> [6/6] Scrubbing PHI (manage.py scrub_staging_phi)"
  for attempt in $(seq 1 30); do
    compose_staging exec -T backend python manage.py check >/dev/null 2>&1 && break
    sleep 2
    [[ "$attempt" -eq 30 ]] && { echo "staging backend never became ready for the scrub step" >&2; exit 6; }
  done
  compose_staging exec -T backend python manage.py scrub_staging_phi --yes-this-is-staging
else
  echo "==> [6/6] No PHI scrub for '$app' (retail ERP data) — nothing to do"
fi

echo "Staging ready: http://localhost:${staging_port}/ (not yet exposed publicly — see this script's header)"
