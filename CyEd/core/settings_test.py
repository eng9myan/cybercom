"""
Settings override for running CyEd's test suite in CI.
Overrides PostgreSQL/Redis with in-memory SQLite/LocMemCache — no external
services. Does NOT touch authentication: tests mint real RS256 JWTs and mock
only the JWKS client (conftest.py's mint_token/mock_jwks), exercising the real
CyIdentityAuthMiddleware validation path end-to-end.
"""

from core.settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# The test client speaks HTTP, so the production HTTPS redirect would turn every
# request into a 301 and test nothing. Disabled here only — `check --deploy`
# still enforces it for real deployments.
SECURE_SSL_REDIRECT = False
