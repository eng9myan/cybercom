"""
No-Docker LOCAL DEV settings for CyEd.

Runs the whole backend with zero external services:
  * PostgreSQL  -> a persistent SQLite file (survives restarts, unlike tests)
  * Redis       -> local-memory cache
  * Celery      -> eager (tasks run inline, synchronously)
  * Keycloak    -> DevAuthMiddleware (fake identity; NO real token needed)

SECURITY: the auth bypass only activates when BOTH DJANGO_DEBUG=True AND
CYED_DEV_AUTH=1. It is impossible to reach through the production settings
module (core.settings), which keeps the real CyIdentityAuthMiddleware.

    Usage:
      set DJANGO_SETTINGS_MODULE=core.settings_dev
      set DJANGO_DEBUG=True
      set CYED_DEV_AUTH=1
      python manage.py migrate
      python manage.py seed_cyed_demo
      python manage.py runserver 8095
"""

import os

from core.settings import *  # noqa: F401,F403

BASE_DIR = globals()["BASE_DIR"]

DEBUG = True
ALLOWED_HOSTS = ["*"]

# The hardening in core.settings is computed from the *environment's* DEBUG at
# import time, so setting DEBUG here afterwards does not undo it. Turned off
# explicitly: without this the dev server 301s its own API to HTTPS, which it
# cannot serve, and every request from the local frontend fails.
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        # Overridable so a load-test seed can run against a scratch database
        # instead of the working dev one — seeding a year of data into the DB
        # you develop against is a slow mistake to undo.
        "NAME": os.environ.get("CYED_DEV_DB", str(BASE_DIR / "cyed_dev.sqlite3")),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CORS_ALLOW_ALL_ORIGINS = True

# Swap the real Keycloak/JWKS auth for the dev shim. Everything else in the
# middleware stack (tenant isolation, etc.) is preserved and still runs.
MIDDLEWARE = [
    ("core.dev_auth.DevAuthMiddleware" if m == "shared.auth.auth_middleware.CyIdentityAuthMiddleware" else m)
    for m in globals()["MIDDLEWARE"]
]

# The fixed dev tenant (matches seed_cyed_demo).
DEV_TENANT_ID = os.environ.get("CYED_DEV_TENANT_ID", "11111111-1111-1111-1111-111111111111")
