"""
Settings override for running Cycom's test suite in CI.
Overrides PostgreSQL/Redis with in-memory SQLite/LocMemCache — no
external services needed. Does NOT touch authentication: cycom's real
tests mint actual RS256 JWTs and mock only the JWKS client itself
(conftest.py's mint_token/mock_jwks), exercising the real
CyIdentityAuthMiddleware validation path end-to-end. Disabling auth
here the way cymed's settings_test.py does would break that pattern.
"""

from core.settings import *

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
