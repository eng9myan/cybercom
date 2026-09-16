"""
Run the test suite against a real PostgreSQL.

`settings_test` uses in-memory SQLite so the suite needs no services. That is
right for the fast loop, but it silently skips everything Postgres-specific —
most importantly **Row-Level Security**, whose migration is a no-op on any
other backend. A suite that only ever runs on SQLite cannot tell you whether
the database-level tenant isolation actually works, which for a multi-school
deployment is the guarantee that matters most.

Point it at any Postgres:

    CYED_TEST_PG_URL=postgresql://user:pass@host:5432/postgres \
    DJANGO_SETTINGS_MODULE=core.settings_test_pg python -m pytest

Kept separate from `settings_test` rather than made conditional so the default
loop stays dependency-free and this one fails loudly when no URL is given.
"""

import os
from urllib.parse import urlparse

from core.settings import *  # noqa: F401,F403

_URL = os.environ.get("CYED_TEST_PG_URL")
if not _URL:
    raise RuntimeError(
        "settings_test_pg needs CYED_TEST_PG_URL "
        "(e.g. postgresql://postgres:@127.0.0.1:5432/postgres)."
    )

_parsed = urlparse(_URL)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": (_parsed.path or "/postgres").lstrip("/"),
        "USER": _parsed.username or "postgres",
        "PASSWORD": _parsed.password or "",
        "HOST": _parsed.hostname or "127.0.0.1",
        "PORT": str(_parsed.port or 5432),
        # The tenant GUC is set per request with SET LOCAL, which only holds
        # inside a transaction. Without ATOMIC_REQUESTS the setting evaporates
        # and every RLS policy silently falls through to its NULL branch.
        "ATOMIC_REQUESTS": True,
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# See settings_test: the test client is HTTP, so the redirect would 301 everything.
SECURE_SSL_REDIRECT = False
