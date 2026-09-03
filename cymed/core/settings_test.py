"""
Settings override for running unit tests on CyberCom Platform.
Overrides PostgreSQL and Redis to use in-memory SQLite and LocMemCache.
"""

from rest_framework.authentication import BaseAuthentication

from core.settings import *


class TestJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        user_session = getattr(request._request, "user_session", None)
        if user_session:

            class MockUser:
                is_authenticated = True
                id = user_session.get("user_id", "test-user")

                def __str__(self):
                    return self.id

            return (MockUser(), None)
        return None


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

# Celery: run tasks inline, never touch a broker/result backend. Without this,
# model post_save signals that call task.delay() (e.g. payments.stamp_bill_task)
# try to reach Redis and stall the suite on a ~20-retry reconnect storm.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# platform.security.middleware.RateLimitMiddleware throttles at 60 req/min/IP.
# Test classes that make many sequential API calls (e.g. the hospital suite)
# blow the bucket and get 429s only when run together, not in isolation.
PLATFORM_RATE_LIMIT_ENABLED = False

# Disable structured JSON logging — pythonjsonlogger may not be installed in test env
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.settings_test.TestJWTAuthentication",
    ],
    # Disable throttling in tests so rate-limited public endpoints
    # (demo-request, contact, newsletter) can be called multiple times
    # without hitting the IP-scoped bucket.
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "website_public_read": "99999/second",
        "website_public_write": "99999/second",
        "website_demo_request": "99999/second",
        "website_contact": "99999/second",
        "website_partner_application": "99999/second",
        "website_newsletter": "99999/second",
    },
}
