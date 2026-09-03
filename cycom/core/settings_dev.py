"""
No-Docker LOCAL DEV settings.

Runs the whole backend with zero external services:
  * PostgreSQL  -> a persistent SQLite file (survives restarts, unlike tests)
  * Redis       -> local-memory cache
  * Celery      -> eager (tasks run inline, synchronously)
  * Keycloak    -> DevAuthMiddleware (fake identity; NO real token needed)

SECURITY: the auth bypass only activates when BOTH DJANGO_DEBUG=True AND
CYCOM_DEV_AUTH=1. It is impossible to reach through the production settings
module (core.settings), which keeps the real CyIdentityAuthMiddleware.

    Usage:
      set DJANGO_SETTINGS_MODULE=core.settings_dev
      set DJANGO_DEBUG=True
      set CYCOM_DEV_AUTH=1
      python manage.py migrate
      python manage.py seed_dev_tenant
      python manage.py seed_packs
      python manage.py runserver 8090
"""

import os

from core.settings import *  # noqa: F401,F403

BASE_DIR = globals()["BASE_DIR"]

DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "cycom_dev.sqlite3"),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# No Keycloak cluster in no-Docker dev. The cyidentity services already ship an
# in-process fake store (_FAKE_KEYCLOAK_STORE) that activates when this is False,
# so realm/client/user provisioning runs fully offline and synchronously. The
# inbound token path is separately handled by DevAuthMiddleware.
KEYCLOAK_ENABLED = False

# Wide-open CORS for the local Next.js dev server on any port.
CORS_ALLOW_ALL_ORIGINS = True

# Swap the real Keycloak/JWKS auth for the dev shim. Everything else in the
# middleware stack (tenant isolation, etc.) is preserved and still runs.
MIDDLEWARE = [
    ("core.dev_auth.DevAuthMiddleware" if m == "shared.auth.auth_middleware.CyIdentityAuthMiddleware" else m)
    for m in globals()["MIDDLEWARE"]
]

# The fixed dev tenant (matches seed_dev_tenant + the Keycloak realm mapper).
DEV_TENANT_ID = os.environ.get("CYCOM_DEV_TENANT_ID", "11111111-1111-1111-1111-111111111111")
