"""
CyberCom Platform — Django Settings
ADR-0001, ADR-0002, ADR-0009, ADR-0034 compliant.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

# ---------------------------------------------------------------------------
# SECURITY
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"] if not os.environ.get("DJANGO_DEBUG", "False") == "True" else os.environ.get("DJANGO_SECRET_KEY", "dev-unsafe-secret-key-do-not-use-in-prod")

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
]

PLATFORM_APPS = [
    "platform.common",
    "platform.tenant",
    "platform.audit",
    "platform.cyidentity",
    "platform.api",
    "platform.events",
    "platform.notifications",
    "platform.cyintegrationhub",
    "platform.cydata",
    "platform.cyai",
    "platform.terminology",
]

PRODUCT_APPS = [
    "products.cymed.core.patients",
    "products.cymed.core.providers",
    "products.cymed.core.organizations",
    "products.cymed.core.facilities",
    "products.cymed.core.encounters",
    "products.cymed.core.clinical",
    "products.cymed.core.documents",
    "products.cymed.core.careplans",
    "products.cymed.core.orders",
    "products.cymed.core.scheduling",
    "products.cymed.core.consents",
    "products.cymed.core.registries",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PLATFORM_APPS + PRODUCT_APPS

# ---------------------------------------------------------------------------
# MIDDLEWARE (order matters — tenant before audit)
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
    "core.middleware.audit.AuditMiddleware",
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
# DATABASE — PostgreSQL 16 with RLS (ADR-0002)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "cybercom_dev"),
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
# CACHE — Redis (ADR-0001)
# ---------------------------------------------------------------------------
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": "cybercom",
        "TIMEOUT": 300,
    }
}

# ---------------------------------------------------------------------------
# CELERY (ADR-0001)
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = int(os.environ.get("CELERY_TASK_TIME_LIMIT", "300"))
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100

# ---------------------------------------------------------------------------
# KAFKA (ADR-0004)
# ---------------------------------------------------------------------------
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_SECURITY_PROTOCOL = os.environ.get("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
KAFKA_SASL_MECHANISM = os.environ.get("KAFKA_SASL_MECHANISM", "")
KAFKA_SASL_USERNAME = os.environ.get("KAFKA_SASL_USERNAME", "")
KAFKA_SASL_PASSWORD = os.environ.get("KAFKA_SASL_PASSWORD", "")
KAFKA_SCHEMA_REGISTRY_URL = os.environ.get("KAFKA_SCHEMA_REGISTRY_URL", "http://localhost:8081")

# ---------------------------------------------------------------------------
# IDENTITY — CyIdentity / Keycloak (ADR-0005)
# ---------------------------------------------------------------------------
CYIDENTITY_ISSUER = os.environ.get("CYIDENTITY_ISSUER", "http://localhost:8080/realms/cybercom")
CYIDENTITY_JWKS_URI = os.environ.get("CYIDENTITY_JWKS_URI", f"{CYIDENTITY_ISSUER}/protocol/openid-connect/certs")
CYIDENTITY_CLIENT_ID = os.environ.get("CYIDENTITY_CLIENT_ID", "cybercom-backend")
JWT_SIGNING_KEY = os.environ.get("JWT_PUBLIC_KEY", "")
JWT_ALGORITHMS = ["RS256"]
JWT_ACCESS_TOKEN_LIFETIME_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_LIFETIME", "15"))

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
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": int(os.environ.get("API_PAGE_SIZE", "25")),
    "EXCEPTION_HANDLER": "platform.api.exceptions.cybercom_exception_handler",
}

# ---------------------------------------------------------------------------
# OPENAPI / SPECTACULAR (ADR-0003)
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "CyberCom Platform API",
    "DESCRIPTION": "CyberCom multi-tenant enterprise platform REST API. OAuth2/OIDC secured.",
    "VERSION": os.environ.get("APP_VERSION", "0.1.0"),
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
    "SECURITY": [{"bearerAuth": []}],
    "SERVERS": [
        {"url": "/api/v1", "description": "Platform API v1"},
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
# INTERNATIONALIZATION (Arabic + English, ADR-0032)
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("en", "English"),
    ("ar", "Arabic"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

# ---------------------------------------------------------------------------
# STATIC & MEDIA
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# LOGGING — structured JSON for OTel collector (ADR-0009)
# ---------------------------------------------------------------------------
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(trace_id)s %(span_id)s",
        },
        "simple": {
            "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "json" if not DEBUG else "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "cybercom": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "cybercom.audit": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# ---------------------------------------------------------------------------
# OPENTELEMETRY (ADR-0009)
# ---------------------------------------------------------------------------
OTEL_ENABLED = os.environ.get("OTEL_ENABLED", "False") == "True"
OTEL_SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "cybercom-platform")
OTEL_SERVICE_VERSION = os.environ.get("APP_VERSION", "0.1.0")
OTEL_EXPORTER_OTLP_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
OTEL_EXPORTER_OTLP_PROTOCOL = os.environ.get("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")

# ---------------------------------------------------------------------------
# MULTI-TENANCY (ADR-0002) — RLS GUC name
# ---------------------------------------------------------------------------
TENANT_GUC_SETTING = "app.current_tenant_id"
TENANT_HEADER = "X-Tenant-ID"
TENANT_BYPASS_PATHS = [
    "/health",
    "/health/liveness",
    "/health/readiness",
    "/api/schema/",
    "/api/docs/",
    "/admin/",
]

# ---------------------------------------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------------------------
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
APP_VERSION = os.environ.get("APP_VERSION", "0.1.0")
