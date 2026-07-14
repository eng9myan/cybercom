"""
CyMart — Django Settings.
Reuses the shared platform/ and shared/ layers promoted in Phase 1
(same pattern as cymed/core/settings.py) rather than reimplementing
identity, tenancy, audit, or events for a fourth product.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ---------------------------------------------------------------------------
# SECURITY
# ---------------------------------------------------------------------------
SECRET_KEY = (
    os.environ["DJANGO_SECRET_KEY"]
    if not os.environ.get("DJANGO_DEBUG", "False") == "True"
    else os.environ.get("DJANGO_SECRET_KEY", "dev-unsafe-secret-key-do-not-use-in-prod")
)

DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# ---------------------------------------------------------------------------
# APPLICATIONS
# ---------------------------------------------------------------------------
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

# Same shared platform layer cymed uses — CyIdentity, tenant, audit,
# events, notifications, API framework. Nothing product-specific
# reimplemented here.
PLATFORM_APPS = [
    "platform.common",
    "platform.tenant",
    "platform.audit",
    "platform.cyidentity",
    "platform.api",
    "platform.events",
    "platform.notifications",
]

PRODUCT_APPS = [
    "products.cymart.commission",
    "products.cymart.catalog",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PLATFORM_APPS + PRODUCT_APPS

# ---------------------------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "shared.auth.auth_middleware.CyIdentityAuthMiddleware",
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

# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "cymart_dev"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# IDENTITY — same CyIdentity realm cymed uses (shared platform, one IdP)
# ---------------------------------------------------------------------------
CYIDENTITY_ISSUER = os.environ.get("CYIDENTITY_ISSUER", "http://localhost:8080/realms/cybercom")
CYIDENTITY_JWKS_URI = os.environ.get(
    "CYIDENTITY_JWKS_URI", f"{CYIDENTITY_ISSUER}/protocol/openid-connect/certs"
)
JWT_SIGNING_KEY = os.environ.get("JWT_PUBLIC_KEY", "")
JWT_ALGORITHMS = ["RS256"]

# ---------------------------------------------------------------------------
# DRF
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "platform.api.pagination.CyberComCursorPagination",
    "EXCEPTION_HANDLER": "platform.api.exceptions.cybercom_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "CyMart API",
    "DESCRIPTION": "CyberCom marketplace orchestration layer. OAuth2/OIDC secured.",
    "VERSION": os.environ.get("APP_VERSION", "0.1.0"),
    "SECURITY": [{"bearerAuth": []}],
    "SERVERS": [{"url": "/api/v1", "description": "CyMart API v1"}],
}

CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000"
).split(",")
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = DEBUG

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
LANGUAGES = [("en", "English"), ("ar", "Arabic")]
