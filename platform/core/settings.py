"""
Standalone Django project for the shared `platform/*` apps.

Exists so the platform layer has its own fast CI job instead of only being
exercised through cycom's / cymed's projects. Test-oriented defaults (SQLite,
LocMemCache, eager Celery, Keycloak fake); every value is env-overridable.

Run:  cd platform && python run_tests.py <app>/tests
"""
import os
from pathlib import Path

from rest_framework.authentication import BaseAuthentication

BASE_DIR = Path(__file__).resolve().parent.parent      # the platform/ dir
REPO_ROOT = BASE_DIR.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "platform-tests-not-a-real-secret")
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
]

# Every platform app that carries models and/or a test suite.
PLATFORM_APPS = [
    "platform.common",
    "platform.tenant",
    "platform.audit",
    "platform.cyidentity",
    "platform.api",
    "platform.events",
    "platform.notifications",
    "platform.provisioning",
    "platform.einvoicing",
    "platform.security",
    "platform.terminology",
    "platform.wallet",
    "platform.cyai",
    "platform.cydata",
    "platform.cyintegrationhub",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PLATFORM_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "shared.auth.auth_middleware.CyIdentityAuthMiddleware",
    "core.middleware.TenantIsolationMiddleware",
    "platform.common.middleware.TenantContextMiddleware",
]

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DB_NAME", ":memory:"),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", ""),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

KEYCLOAK_ENABLED = False
PLATFORM_RATE_LIMIT_ENABLED = False

# CyIdentity / JWT — the conftest mints RS256 tokens and patches the JWKS client.
CYIDENTITY_ISSUER = os.environ.get("CYIDENTITY_ISSUER", "http://localhost:8080/realms/cybercom")
CYIDENTITY_JWKS_URI = f"{CYIDENTITY_ISSUER}/protocol/openid-connect/certs"
CYIDENTITY_CLIENT_ID = os.environ.get("CYIDENTITY_CLIENT_ID", "cybercom-backend")
JWT_ALGORITHMS = ["RS256"]

# Row-level security + per-tenant field encryption (platform.security / .common).
RLS_ENFORCED = os.environ.get("PLATFORM_RLS_ENFORCED", "0") == "1"
TENANT_GUC_SETTING = os.environ.get("TENANT_GUC_SETTING", "app.current_tenant_id")
FIELD_ENCRYPTION_KEY = os.environ.get(
    "FIELD_ENCRYPTION_KEY",
    # base64(sha256(b"cybercom-dev-field-key-platform")) — dev only
    "0Bc0Yb3F8vQ2s1nJqf0m5S7wU9r4tXeH2aKpL6dZ0oE=",
)

class TestJWTAuthentication(BaseAuthentication):
    """Turns the `request.user_session` that CyIdentityAuthMiddleware builds
    from the JWT into an authenticated DRF user, so `IsAuthenticated`-gated
    endpoints are reachable with a minted test token (mirrors cymed's
    core.settings_test.TestJWTAuthentication)."""

    def authenticate(self, request):
        session = getattr(request._request, "user_session", None)
        if not session:
            return None

        class MockUser:
            is_authenticated = True
            id = session.get("user_id", "test-user")

            def __str__(self):
                return str(self.id)

        return (MockUser(), None)


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["core.settings.TestJWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "EXCEPTION_HANDLER": "platform.api.exceptions.cybercom_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "website_demo_request": "20/hour",
        "website_public_write": "30/hour",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "CyberCom Platform API",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "WARNING")},
}
