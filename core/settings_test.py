"""
Settings override for running unit tests on CyberCom Platform.
Overrides PostgreSQL and Redis to use in-memory SQLite and LocMemCache.
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

KEYCLOAK_ENABLED = False

