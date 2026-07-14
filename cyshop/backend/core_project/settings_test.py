"""
Settings override for running CyShop backend tests without a live Postgres.
Mirrors cymed/core/settings_test.py's pattern.
"""

from core_project.settings import *  # noqa: F401,F403

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
