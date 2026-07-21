"""
Settings override for running CyVault's test suite in CI.
Overrides PostgreSQL/Redis with in-memory SQLite/LocMemCache, and object
storage with a real (but throwaway, per-test-run) local temp directory —
django.core.files.storage.FileSystemStorage is exercised for real here,
not mocked, so upload/download round-trips are genuinely verified.
Does NOT touch authentication — same rationale as cycom/core/settings_test.py.
"""

import tempfile

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

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
MEDIA_ROOT = tempfile.mkdtemp(prefix="cyvault-test-media-")
