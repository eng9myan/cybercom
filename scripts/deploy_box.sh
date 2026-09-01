#!/usr/bin/env bash
# CyCom single-box production deploy — run ON the fresh Ubuntu VM, from the
# repo root:  bash scripts/deploy_box.sh
#
# Assumes (done by the operator BEFORE running):
#   * DNS A-records app.cy-com.com + auth.cy-com.com -> this box's public IP
#     (DNS-only / grey-cloud so Let's Encrypt HTTP-01 can validate).
#   * Ports 22, 80, 443 open (OCI security list/NSG + the box firewall).
#
# Idempotent: re-running reuses the generated secrets in infrastructure/.env
# (so DB passwords don't drift). It generates all infra secrets locally; it
# never asks for or handles any of your personal credentials.
set -euo pipefail

APP_DOMAIN=app.cy-com.com
AUTH_DOMAIN=auth.cy-com.com
ADMIN_EMAIL=admin@cy-com.com
COMPOSE=infrastructure/docker-compose.prod-box.yml
ENVF=infrastructure/.env

cd "$(dirname "$0")/.."   # repo root

echo "==> [1/7] Docker"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sudo sh
fi
DC() { sudo docker compose -f "$COMPOSE" --env-file "$ENVF" "$@"; }

echo "==> [2/7] Secrets + env files"
gen() { openssl rand -hex 24; }
if [ ! -f "$ENVF" ]; then
  DJANGO_SECRET_KEY=$(openssl rand -hex 48)
  DB_PASSWORD=$(gen); REDIS_PASSWORD=$(gen)
  KC_DB_PASSWORD=$(gen); KC_ADMIN_PASSWORD=$(gen)
  cat > "$ENVF" <<EOF
# compose interpolation + infra secrets (generated $(date -u +%FT%TZ))
AUTH_DOMAIN=$AUTH_DOMAIN
APP_DOMAIN=$APP_DOMAIN
KC_DB_USERNAME=kcadmin
KC_DB_PASSWORD=$KC_DB_PASSWORD
KC_ADMIN_USERNAME=admin
KC_ADMIN_PASSWORD=$KC_ADMIN_PASSWORD
DB_NAME=cycom
DB_USER=cycom
DB_PASSWORD=$DB_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
EOF
  chmod 600 "$ENVF"
  echo "    generated $ENVF"
else
  echo "    reusing existing $ENVF"
fi
# shellcheck disable=SC1090
set -a; . "$ENVF"; set +a

cat > infrastructure/.env.production <<EOF
DJANGO_SETTINGS_MODULE=core.settings
DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
DJANGO_DEBUG=False
ALLOWED_HOSTS=backend,cybercom-backend,localhost,127.0.0.1,$APP_DOMAIN
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=cycom-postgres
DB_PORT=5432
REDIS_URL=redis://:$REDIS_PASSWORD@cycom-redis:6379/0
CELERY_BROKER_URL=redis://:$REDIS_PASSWORD@cycom-redis:6379/1
CELERY_RESULT_BACKEND=redis://:$REDIS_PASSWORD@cycom-redis:6379/1
CYIDENTITY_ISSUER=https://$AUTH_DOMAIN/realms/cybercom
CYIDENTITY_JWKS_URI=http://keycloak:8080/realms/cybercom/protocol/openid-connect/certs
CYIDENTITY_CLIENT_ID=cybercom-backend
KEYCLOAK_ADMIN=$KC_ADMIN_USERNAME
KEYCLOAK_ADMIN_PASSWORD=$KC_ADMIN_PASSWORD
CYCOM_DEV_AUTH=0
CYCOM_PAYMENT_PROVIDER=manual
CORS_ALLOWED_ORIGINS=https://$APP_DOMAIN
ENVIRONMENT=production
APP_VERSION=1.0.0
EOF
chmod 600 infrastructure/.env.production

# Frontend env — CLIENT_SECRET filled after bootstrap (step 6).
if [ ! -f infrastructure/.env.frontend ]; then
  cat > infrastructure/.env.frontend <<EOF
NODE_ENV=production
CYCOM_BACKEND_URL=http://backend:8000
KEYCLOAK_TOKEN_URL=http://keycloak:8080/realms/cybercom/protocol/openid-connect/token
KEYCLOAK_CLIENT_ID=cybercom-backend
KEYCLOAK_CLIENT_SECRET=PENDING
CYCOM_DEV_AUTH=0
CYCOM_TENANT_ID=
NEXT_PUBLIC_APP_URL=https://$APP_DOMAIN
EOF
  chmod 600 infrastructure/.env.frontend
fi

echo "==> [3/7] Build + start infra (db, redis, keycloak, backend, caddy)"
DC build backend
DC up -d keycloak-db cycom-postgres cycom-redis keycloak backend caddy

echo "==> [4/7] Wait for Keycloak TLS via Caddy (issues Let's Encrypt cert)"
ok=0
for i in $(seq 1 40); do
  if DC exec -T backend curl -fsS "https://$AUTH_DOMAIN/realms/cybercom/.well-known/openid-configuration" >/dev/null 2>&1; then
    ok=1; echo "    TLS + realm reachable"; break
  fi
  echo "    ($i/40) waiting for cert + realm import..."; sleep 15
done
[ "$ok" = 1 ] || { echo "!! Keycloak/TLS not ready. Check: DNS -> this box, ports 80/443 open, 'sudo docker logs cybercom-caddy'"; exit 1; }

echo "==> [5/7] Backend migrate / collectstatic / seed"
DC exec -T backend python manage.py migrate --noinput
DC exec -T backend python manage.py collectstatic --noinput || true
DC exec -T backend python manage.py seed_packs || true

echo "==> [6/7] Bootstrap platform realm (capture client secret + admin creds)"
BOOT=$(DC exec -T backend python manage.py bootstrap_platform_realm --admin-email "$ADMIN_EMAIL" --admin-username platformadmin)
echo "$BOOT"
CLIENT_SECRET=$(printf '%s\n' "$BOOT" | sed -n 's/.*Client secret: *//p' | tr -d '\r' | head -1)
PLAT_PASS=$(printf '%s\n' "$BOOT" | sed -n 's/.*Admin password: *//p' | tr -d '\r' | head -1)
if [ -n "$CLIENT_SECRET" ]; then
  sed -i "s|^KEYCLOAK_CLIENT_SECRET=.*|KEYCLOAK_CLIENT_SECRET=$CLIENT_SECRET|" infrastructure/.env.frontend
  echo "    injected client secret into frontend env"
else
  echo "!! could not parse client secret from bootstrap output — set KEYCLOAK_CLIENT_SECRET in infrastructure/.env.frontend manually"
fi

echo "==> [7/7] Build + start frontend"
DC build frontend
DC up -d frontend

echo
echo "############################################################"
echo "CyCom is live."
echo "  App:        https://$APP_DOMAIN"
echo "  Auth:       https://$AUTH_DOMAIN"
echo "  KC admin:   user 'admin' / pass in infrastructure/.env (KC_ADMIN_PASSWORD)"
echo "  Platform admin: platformadmin / ${PLAT_PASS:-see bootstrap output above}"
echo "  Payments:   manual (bank transfer). Set CYCOM_PAYMENT_PROVIDER + STRIPE_* to go online."
echo "  Secrets live in infrastructure/.env* (chmod 600, git-ignored)."
echo "############################################################"
DC ps
