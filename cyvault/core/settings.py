"""
CyVault (object storage / DICOM archiving) — Django Settings.
Mirrors cycom/core/settings.py conventions, trimmed to this product's scope.

Named "CyVault", not "CyDrive" — CyDrive already exists in this repo as a
real, live delivery-dispatch/fleet product (D:\\cybercom\\cydrive, consumed
by cymart's cydrive_client.py). This product is unrelated (cloud storage,
not logistics) and needed a different name to avoid the collision.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

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

# Real request-body size ceiling for file uploads — Django's default
# DATA_UPLOAD_MAX_MEMORY_SIZE (2.5MB) would silently reject any DICOM
# study or catalog-image upload larger than that with a 400 before this
# app's own per-field validation ever runs.
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get("CYVAULT_MAX_UPLOAD_BYTES", str(200 * 1024 * 1024)))
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get("CYVAULT_MAX_UPLOAD_BYTES", str(200 * 1024 * 1024)))

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

PLATFORM_APPS = [
    "platform.common",
    "platform.tenant",
    "platform.cyidentity",
    "platform.api",
]

PRODUCT_APPS = [
    "products.cyvault.files",
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
    "core.middleware.tenant.TenantIsolationMiddleware",
]

ROOT_URLCONF = "core.urls"

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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
# DATABASE — PostgreSQL 16
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "cyvault"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "OPTIONS": {
            "connect_timeout": 10,
            "options": "-c search_path=public",
        },
        "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
        "CONN_HEALTH_CHECKS": True,
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# CACHE — Redis
# ---------------------------------------------------------------------------
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": "cyvault",
        "TIMEOUT": 300,
    }
}

# ---------------------------------------------------------------------------
# IDENTITY — CyIdentity / Keycloak, shared realm from Phase A
# ---------------------------------------------------------------------------
CYIDENTITY_ISSUER = os.environ.get("CYIDENTITY_ISSUER", "http://localhost:8080/realms/cybercom")
CYIDENTITY_JWKS_URI = os.environ.get(
    "CYIDENTITY_JWKS_URI", f"{CYIDENTITY_ISSUER}/protocol/openid-connect/certs"
)
CYIDENTITY_CLIENT_ID = os.environ.get("CYIDENTITY_CLIENT_ID", "cybercom-backend")

# ---------------------------------------------------------------------------
# DRF — Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": int(os.environ.get("API_PAGE_SIZE", "25")),
    "EXCEPTION_HANDLER": "platform.api.exceptions.cybercom_exception_handler",
}

# ---------------------------------------------------------------------------
# OPENAPI / SPECTACULAR
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "CyVault API",
    "DESCRIPTION": "CyVault (CyberCom's object storage / DICOM archiving product) REST API.",
    "VERSION": os.environ.get("APP_VERSION", "0.1.0"),
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
    "SECURITY": [{"bearerAuth": []}],
    "SERVERS": [
        {"url": "/api/v1", "description": "CyVault API v1"},
    ],
}

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001"
).split(",")
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = DEBUG

# ---------------------------------------------------------------------------
# INTERNATIONALIZATION
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# STATIC & OBJECT STORAGE
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Pluggable storage backend: local filesystem by default (dev/test — no
# external dependency needed to run this app or its test suite), real
# S3-compatible object storage (AWS S3 or self-hosted MinIO, both speak the
# same S3 API) in production via env var. This IS the real "CyVault
# storage abstraction" — everything else (FileObject model, presigned
# download URLs) is just Django's own FileField/`.url()` on top of
# whichever backend is configured here; django-storages' S3Boto3Storage
# generates real presigned URLs automatically when AWS_QUERYSTRING_AUTH
# is enabled (its default) against a private bucket.
CYVAULT_STORAGE_BACKEND = os.environ.get(
    "CYVAULT_STORAGE_BACKEND", "django.core.files.storage.FileSystemStorage"
)
STORAGES = {
    "default": {"BACKEND": CYVAULT_STORAGE_BACKEND},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
MEDIA_URL = os.environ.get("CYVAULT_MEDIA_URL", "/media/")
MEDIA_ROOT = BASE_DIR / "media"  # only used when the FileSystemStorage default is active

# S3Boto3Storage settings — read only when CYVAULT_STORAGE_BACKEND selects
# it; harmless no-ops (unused settings) under the FileSystemStorage default.
AWS_ACCESS_KEY_ID = os.environ.get("CYVAULT_S3_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("CYVAULT_S3_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.environ.get("CYVAULT_S3_BUCKET", "cyvault")
AWS_S3_ENDPOINT_URL = os.environ.get("CYVAULT_S3_ENDPOINT_URL", "")  # e.g. http://minio:9000 for self-hosted
AWS_S3_REGION_NAME = os.environ.get("CYVAULT_S3_REGION", "us-east-1")
AWS_DEFAULT_ACL = None  # private by default — access only via presigned URLs
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = int(os.environ.get("CYVAULT_PRESIGNED_URL_TTL_SECONDS", "3600"))
AWS_S3_ADDRESSING_STYLE = "path"  # required by most self-hosted MinIO deployments

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}

# ---------------------------------------------------------------------------
# MULTI-TENANCY
# ---------------------------------------------------------------------------
TENANT_GUC_SETTING = "app.current_tenant_id"
TENANT_HEADER = "X-Tenant-ID"

# ---------------------------------------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------------------------
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
APP_VERSION = os.environ.get("APP_VERSION", "0.1.0")
