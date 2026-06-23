"""
Settings override for running unit tests on CyberCom Platform.
Overrides PostgreSQL and Redis to use in-memory SQLite and LocMemCache.
"""
from core.settings import *
from rest_framework.authentication import BaseAuthentication

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
}

