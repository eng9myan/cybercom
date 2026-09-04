"""
Cycom (from-scratch backend) — Django Settings.
Mirrors cymed/core/settings.py conventions, trimmed to this product's scope.
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
    "platform.audit",
    "platform.cyidentity",
    "platform.api",
    "platform.events",
    "platform.cyai",
    "platform.provisioning",
    "platform.einvoicing",
]

PRODUCT_APPS = [
    "products.cycom.accounting",
    "products.cycom.ar_ap",
    "products.cycom.hr",
    "products.cycom.payroll",
    "products.cycom.inventory",
    "products.cycom.catalog",
    "products.cycom.access",
    "products.cycom.pos",
    "products.cycom.crm",
    "products.cycom.procurement",
    "products.cycom.cyai_memory",
    "products.cycom.cyai_reports",
    "products.cycom.cyai_moduledev",
    "products.cycom.cyai_analytics",
    "products.cycom.cyai_platform",
    "products.cycom.documents",
    "products.cycom.expenses",
    "products.cycom.scheduler",
    "products.cycom.notes",
    "products.cycom.todo",
    "products.cycom.knowledge",
    "products.cycom.manufacturing",
    "products.cycom.maintenance",
    "products.cycom.quality",
    "products.cycom.field_service",
    "products.cycom.subscriptions",
    "products.cycom.equity",
    "products.cycom.esg",
    "products.cycom.localization",
    "products.cycom.fleet",
    "products.cycom.sales",
    "products.cycom.helpdesk",
    "products.cycom.recruitment",
    "products.cycom.leave",
    "products.cycom.project",
    "products.cycom.marketing",
    "products.cycom.planning",
    "products.cycom.plm",
    "products.cycom.discuss",
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
        "NAME": os.environ.get("DB_NAME", "cycom_new"),
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
        "KEY_PREFIX": "cycom",
        "TIMEOUT": 300,
    }
}

# ---------------------------------------------------------------------------
# CELERY — DB index 1, separate from cymed's default /0, to avoid queue
# collisions on the shared cybercom-redis container.
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/1")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True

# ---------------------------------------------------------------------------
# IDENTITY — CyIdentity / Keycloak, shared realm from Phase A
# ---------------------------------------------------------------------------
CYIDENTITY_ISSUER = os.environ.get("CYIDENTITY_ISSUER", "http://localhost:8080/realms/cybercom")
CYIDENTITY_JWKS_URI = os.environ.get(
    "CYIDENTITY_JWKS_URI", f"{CYIDENTITY_ISSUER}/protocol/openid-connect/certs"
)
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
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # django_filters was installed but never actually wired as a filter
    # backend — every ?field=value query param used against any viewset
    # this session was silently ignored (returned the full unfiltered
    # queryset). Confirmed as a real bug via cy.internal.order.line
    # returning every tenant's lines mixed together instead of one order's.
    # This enables the mechanism; individual viewsets still need
    # filterset_fields to opt in.
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": int(os.environ.get("API_PAGE_SIZE", "25")),
    "EXCEPTION_HANDLER": "platform.api.exceptions.cybercom_exception_handler",
    # Rates for the anon-scoped public signup endpoints (platform.tenant views
    # demo_provision / subscription_register). Without these the AnonRateThrottle
    # subclasses raise ImproperlyConfigured("No default throttle rate set...").
    "DEFAULT_THROTTLE_RATES": {
        "website_demo_request": os.environ.get("THROTTLE_DEMO_REQUEST", "20/hour"),
        "website_public_write": os.environ.get("THROTTLE_PUBLIC_WRITE", "30/hour"),
    },
}

# ---------------------------------------------------------------------------
# OPENAPI / SPECTACULAR
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "Cycom API",
    "DESCRIPTION": "Cycom (CyberCom's own ERP engine) REST API. OAuth2/OIDC secured.",
    "VERSION": os.environ.get("APP_VERSION", "0.1.0"),
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
    "SECURITY": [{"bearerAuth": []}],
    "SERVERS": [
        {"url": "/api/v1", "description": "Cycom API v1"},
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
# MULTI-TENANCY — RLS GUC name (application-layer scoping; no DB RLS policies
# exist anywhere in this codebase yet, so get_queryset() filtering is load-bearing)
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

# ---------------------------------------------------------------------------
# COMPLIANCE GATEWAY — CyID ecosystem, Phase 6 (multi-country billing)
# ---------------------------------------------------------------------------
# compliance-gateway/main.py's real EventBus subscription is dead code
# (imports core-kernel's `bus` module, which was fully decommissioned —
# see Step 9 of the earlier Cycom rebuild; falls back to EventBus=None,
# so nothing was ever actually delivered to it that way). It still exposes
# a real, working direct REST endpoint for exactly this — the standalone
# invoice-posting call below uses that, not a resurrected event bus.
COMPLIANCE_GATEWAY_URL = os.environ.get("COMPLIANCE_GATEWAY_URL", "http://localhost:9000")
COMPLIANCE_GATEWAY_TIMEOUT_SECONDS = int(os.environ.get("COMPLIANCE_GATEWAY_TIMEOUT_SECONDS", "10"))

# ---------------------------------------------------------------------------
# PAYMENTS — provider-agnostic self-serve subscription checkout
# ---------------------------------------------------------------------------
# Active provider: "manual" (bank transfer, finance-confirmed — no keys needed),
# or an online gateway once its account exists ("stripe" is a ready reference
# integration; "paddle"/"hyperpay" are seams to fill). See platform.tenant.payments.
PAYMENT_PROVIDER = os.environ.get("CYCOM_PAYMENT_PROVIDER", "manual")

# Shown to customers when the manual (bank-transfer) provider is active.
BANK_TRANSFER_DETAILS = {
    "beneficiary": os.environ.get("BANK_BENEFICIARY", "CyberCom"),
    "bank": os.environ.get("BANK_NAME", ""),
    "iban": os.environ.get("BANK_IBAN", ""),
    "swift": os.environ.get("BANK_SWIFT", ""),
}

# Stripe (only used when CYCOM_PAYMENT_PROVIDER=stripe). Secret key never leaves
# the backend; only the publishable key is exposed via the pricing endpoint.
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Optional owner override of launch list prices without a code change; see
# platform.tenant.services._DEFAULT_PRICING for the shape.
SUBSCRIPTION_PRICING = None
