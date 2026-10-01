"""
No-Docker LOCAL DEV settings — mirrors cycom/core/settings_dev.py and
CyEd/core/settings_dev.py for this project family.

Runs the whole backend with zero external services:
  * PostgreSQL  -> a persistent SQLite file (survives restarts, unlike tests)
  * Keycloak    -> DevAuthMiddleware (fake identity; NO real token needed)

SECURITY: the auth bypass only activates when BOTH DJANGO_DEBUG=True AND
CYMART_DEV_AUTH=1. It is impossible to reach through the production
settings module (core.settings), which keeps the real
CyIdentityAuthMiddleware.

    Usage:
      set DJANGO_SETTINGS_MODULE=core.settings_dev
      set DJANGO_DEBUG=True
      set CYMART_DEV_AUTH=1
      set DJANGO_SECRET_KEY=dev-secret
      python manage.py migrate
      python manage.py runserver 8000
"""

from core.settings import *  # noqa: F401,F403

BASE_DIR = globals()["BASE_DIR"]

DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "cymart_dev.sqlite3"),
    }
}

# Wide-open CORS for the local Next.js dev server on any port.
CORS_ALLOW_ALL_ORIGINS = True

# Swap the real Keycloak/JWKS auth for the dev shim. Everything else in
# the middleware stack is preserved and still runs.
MIDDLEWARE = [
    ("core.dev_auth.DevAuthMiddleware" if m == "shared.auth.auth_middleware.CyIdentityAuthMiddleware" else m)
    for m in globals()["MIDDLEWARE"]
]

# DRF's own auth layer is separate from the middleware — IsAuthenticated
# checks request.user, not request.user_session. Same pairing
# core.settings_test uses for pytest (TestJWTAuthentication).
REST_FRAMEWORK = {
    **globals()["REST_FRAMEWORK"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["core.dev_auth.DevSessionAuthentication"],
}
