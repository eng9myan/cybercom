# Keycloak on a real box — production bring-up (P0 launch enabler)

This is what unblocks **self-serve signup/login** for CyCom. In the no-Docker dev
path, `register`/`demo` fail at realm provisioning because there's no Keycloak;
standing this up on a real host closes that gap.

Artifacts:
- `../docker-compose.keycloak-prod.yml` — prod-mode Keycloak + dedicated Postgres.
- `../.env.keycloak.example` — secrets template.
- `cycom-dev-realm.json` — the shared `cybercom` realm (client `cybercom-backend`,
  `tenant_id` token mapper). Reused as the import source; rename/trim for prod if desired.

> Verification note: this can only be verified on a real host with a domain +
> TLS. It is intentionally NOT runnable in the local no-Docker path.

## 1. Prerequisites
- A Linux host with Docker + Docker Compose.
- A DNS record: `auth.cy-com.com` → the host.
- A reverse proxy (nginx/Caddy/Traefik) terminating TLS and proxying
  `https://auth.cy-com.com` → `127.0.0.1:8080`.

## 2. Configure secrets
```bash
cd infrastructure
cp .env.keycloak.example .env.keycloak
# edit .env.keycloak: KC_HOSTNAME, KC_DB_PASSWORD, KC_ADMIN_PASSWORD (long/random)
```

## 3. Bring it up
```bash
docker compose -f docker-compose.keycloak-prod.yml --env-file .env.keycloak up -d
docker compose -f docker-compose.keycloak-prod.yml logs -f keycloak   # watch first boot + realm import
```
First boot imports the `cybercom` realm. Health: `curl -f http://127.0.0.1:8080/health/ready`.

## 4. Reverse proxy (example: Caddy)
```
auth.cy-com.com {
    reverse_proxy 127.0.0.1:8080
}
```
(Any proxy works — the key is TLS at the edge and forwarding X-Forwarded-* headers,
which `KC_PROXY_HEADERS=xforwarded` already expects.)

## 5. Set the backend client secret
The `cybercom-backend` client is confidential (client_credentials grant).
1. Admin console → Clients → `cybercom-backend` → Credentials → regenerate secret.
2. Put it in the app environment (do NOT hardcode):
   - `KEYCLOAK_CLIENT_SECRET=<the secret>`

## 6. Point the apps at prod Keycloak
Set these env vars for the Django backend(s) and the Next.js frontend:
```
CYIDENTITY_ISSUER=https://auth.cy-com.com/realms/cybercom
CYIDENTITY_JWKS_URI=https://auth.cy-com.com/realms/cybercom/protocol/openid-connect/certs
KEYCLOAK_TOKEN_URL=https://auth.cy-com.com/realms/cybercom/protocol/openid-connect/token
KEYCLOAK_CLIENT_ID=cybercom-backend
KEYCLOAK_CLIENT_SECRET=<from step 5>
```
Turn OFF the dev shim in prod: ensure `CYCOM_DEV_AUTH` is unset/0 so the real
`CyIdentityAuthMiddleware` (JWKS validation) is used, not `dev_auth`.

## 7. Bootstrap the platform realm from the app
Once Keycloak is reachable, initialize the shared realm/admin the services expect:
```bash
python manage.py bootstrap_platform_realm --admin-email you@cy-com.com --admin-username platformadmin
```
(This is the command that timed out in no-Docker because there was no Keycloak.)

## 8. Verify the loop
- `POST /api/v1/tenants/register/` should now return `201` with a real `realm_name`
  (no more `IdentityRealm.DoesNotExist`).
- The `/signup` page's payment step (bank instructions / gateway redirect) then
  leads to activation via the payment webhook.

## Hardening checklist (before real customers)
- [ ] Rotate the bootstrap admin; create a named admin; disable/rotate the bootstrap creds.
- [ ] Real client secret set (step 5), never committed.
- [ ] TLS enforced end-to-end; HTTP only on the internal proxy hop.
- [ ] `KC_DB_PASSWORD` / `KC_ADMIN_PASSWORD` are long and unique.
- [ ] Backups of the `kc_pgdata` volume (realm + users live here).
- [ ] Realm token lifespans + brute-force protection reviewed in the admin console.
