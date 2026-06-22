"""
Test settings override — uses SQLite (no PostgreSQL needed) and dummy cache.
ADR-0034: Django 5 / Python 3.12. Tests run with KEYCLOAK_ENABLED=False.
"""
from .settings import *  # noqa: F401, F403

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

# Disable Keycloak — use in-memory fake
KEYCLOAK_ENABLED = False

# Faster password hashing in tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable Celery task execution in tests — call synchronously
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Minimal logging
LOGGING = {}
