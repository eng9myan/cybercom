# platform.security

Security hardening primitives shared across the CyberCom / CyMed platform:

| Layer | Module | What it does |
|---|---|---|
| HTTP headers | `middleware.SecurityHeadersMiddleware` | HSTS, CSP, nosniff, deny-frame, referrer, permissions |
| Mobile trust | `middleware.ClientIntegrityMiddleware` | Consume Play-Integrity / App-Attest tokens |
| Abuse control | `middleware.RateLimitMiddleware` | Per-IP token-bucket via `django.core.cache` |
| Key custody | `keys.get_keystore()` | Local dev + AWS KMS backends, Azure / GCP stubs |
| Multi-tenant | `rls.enforce_tenant_scope`, `rls.tenant_context` | ORM guard + PG session GUC for RLS |

## Enabling the middleware

`platform.security` is installed automatically via `INSTALLED_APPS`. Add the
middleware in `core/settings.py`; the recommended order (already applied) is:

```python
MIDDLEWARE = [
    "platform.observability.middleware.RequestIdMiddleware",
    "platform.observability.middleware.AccessLogMiddleware",
    "platform.security.middleware.SecurityHeadersMiddleware",
    "platform.security.middleware.ClientIntegrityMiddleware",
    "platform.security.middleware.RateLimitMiddleware",
    # ...existing Django, auth, tenant, audit middleware
]
```

### Threat model per middleware

| Middleware | Mitigates |
|---|---|
| SecurityHeadersMiddleware | SSL-strip / downgrade (HSTS), clickjacking (`X-Frame-Options`), MIME confusion (`nosniff`), URL leaks (`Referrer-Policy`), inline / third-party script injection (CSP), sensor abuse (Permissions-Policy) |
| ClientIntegrityMiddleware | Rooted / jailbroken / emulated / repackaged clients when combined with server-side attestation verification |
| RateLimitMiddleware | Credential-stuffing, scraping, and cheap-DoS on `/api/*` |

## Configuration

All settings live on `django.conf.settings` and read `os.environ`:

| Setting | Env var | Default |
|---|---|---|
| `PLATFORM_ENFORCE_INTEGRITY` | `PLATFORM_ENFORCE_INTEGRITY` | `False` |
| `PLATFORM_INTEGRITY_EXEMPT_PATHS` | — | `/health`, `/metrics`, `/admin/`, `/api/schema/`, ... |
| `PLATFORM_RATE_LIMIT_ENABLED` | `PLATFORM_RATE_LIMIT_ENABLED` | `True` |
| `PLATFORM_RATE_LIMIT_PER_MIN` | `PLATFORM_RATE_LIMIT_PER_MIN` | `60` |
| `PLATFORM_RATE_LIMIT_ADMIN_PER_MIN` | `PLATFORM_RATE_LIMIT_ADMIN_PER_MIN` | `500` |
| `PLATFORM_KMS_BACKEND` | `PLATFORM_KMS_BACKEND` | `local_dev` |
| `PLATFORM_KEY_DIR` | `PLATFORM_KEY_DIR` | `~/.cybercom/dev-keys` |
| `PLATFORM_SECURITY_HEADERS` | — | `dict` override |

## Key custody upgrade path

Development uses `LocalDevKeyStore` — ECDSA P-256 signing keys and AES-GCM
wrap keys stored unencrypted on disk. **Never enable this in production.**

For staging / production choose a real HSM-backed backend:

| Backend | `PLATFORM_KMS_BACKEND` | Status |
|---|---|---|
| AWS KMS | `aws_kms` | Ready — requires `boto3` and IAM `kms:Sign / Verify / Encrypt / Decrypt` |
| Azure Key Vault | `azure_key_vault` | Stub — see `docs/security/kms-onboarding.md` |
| GCP KMS | `gcp_kms` | Stub — see `docs/security/kms-onboarding.md` |

The `KeyStore` interface is bytes-in / bytes-out and identical across
backends: swap the env var, rotate the key ids, redeploy — application code
does not change.

## RLS helpers

```python
from platform.security.rls import enforce_tenant_scope, tenant_context

# In a view
qs = enforce_tenant_scope(request, Encounter.objects.all())

# In a Celery task
with tenant_context(job.tenant_id):
    run_billing_job(job)
```

`set_tenant_guc()` writes `app.current_tenant_id` on the PG connection so
row-level-security policies defined in migrations can enforce isolation at
the database layer as a second line of defence.
