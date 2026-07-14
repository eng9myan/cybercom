"""Settings override for running CyMart tests without live Postgres/Keycloak."""

from rest_framework.authentication import BaseAuthentication

from core.settings import *  # noqa: F401,F403


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

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_AUTHENTICATION_CLASSES": ["core.settings_test.TestJWTAuthentication"],
}
