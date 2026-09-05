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
    "platform.canonical",
    "platform.tenant",
    "platform.audit",
    "platform.cyidentity",
    "platform.wallet",
    "platform.api",
    "platform.events",
    "platform.notifications",
    "platform.cyintegrationhub",
    "platform.cydata",
    "platform.cyai",
    "platform.terminology",
    "platform.security",
    "platform.observability",
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
    # CyMed Commercial Foundation (Program 3.C0)
    "products.cymed.commercial.licensing",
    "products.cymed.commercial.editions",
    "products.cymed.commercial.feature_flags",
    "products.cymed.commercial.subscriptions",
    "products.cymed.commercial.branding",
    "products.cymed.commercial.deployment_profiles",
    "products.cymed.commercial.product_catalog",
    "products.cymed.commercial.usage_metering",
    "products.cymed.commercial.customer_management",
    "products.cymed.commercial.partner_management",
    # CyMed Clinic Edition (Program 3.1)
    "products.cymed.clinic.reception",
    "products.cymed.clinic.appointments",
    "products.cymed.clinic.consultations",
    "products.cymed.clinic.triage",
    "products.cymed.clinic.telemedicine",
    "products.cymed.clinic.referrals",
    "products.cymed.clinic.queues",
    "products.cymed.clinic.specialties",
    "products.cymed.clinic.clinical_forms",
    "products.cymed.clinic.billing_bridge",
    "products.cymed.clinic.insurance_bridge",
    # CyMed Hospital Edition (Program 3.2)
    "products.cymed.hospital.adt",
    "products.cymed.hospital.bed_management",
    "products.cymed.hospital.emergency",
    "products.cymed.hospital.inpatient",
    "products.cymed.hospital.nursing",
    "products.cymed.hospital.icu",
    "products.cymed.hospital.operating_room",
    "products.cymed.hospital.anesthesia",
    "products.cymed.hospital.maternity",
    "products.cymed.hospital.transfer_center",
    "products.cymed.hospital.discharge",
    "products.cymed.hospital.clinical_command_center",
    "products.cymed.hospital.capacity_management",
    # CyMed Laboratory Edition (Program 3.3)
    "products.cymed.laboratory.orders",
    "products.cymed.laboratory.specimens",
    "products.cymed.laboratory.accessioning",
    "products.cymed.laboratory.worklists",
    "products.cymed.laboratory.results",
    "products.cymed.laboratory.microbiology",
    "products.cymed.laboratory.pathology",
    "products.cymed.laboratory.histopathology",
    "products.cymed.laboratory.quality",
    "products.cymed.laboratory.blood_bank_foundation",
    "products.cymed.laboratory.analytics",
    "products.cymed.laboratory.reference_lab",
    # CyMed Imaging Edition (Program 3.4)
    "products.cymed.imaging.orders",
    "products.cymed.imaging.modality_worklist",
    "products.cymed.imaging.scheduling",
    "products.cymed.imaging.radiology_reporting",
    "products.cymed.imaging.results",
    "products.cymed.imaging.pacs_gateway",
    "products.cymed.imaging.dicom_registry",
    "products.cymed.imaging.teleradiology",
    "products.cymed.imaging.quality",
    "products.cymed.imaging.analytics",
    # CyMed Pharmacy Edition (Program 3.5)
    "products.cymed.pharmacy.prescriptions",
    "products.cymed.pharmacy.dispensing",
    "products.cymed.pharmacy.clinical_pharmacy",
    "products.cymed.pharmacy.medication_reconciliation",
    "products.cymed.pharmacy.drug_interactions",
    "products.cymed.pharmacy.formulary",
    "products.cymed.pharmacy.automation",
    "products.cymed.pharmacy.analytics",
    "products.cymed.pharmacy.inventory_bridge",
    "products.cymed.pharmacy.procurement_bridge",
    # CyMed Integrations
    "products.cymed.integrations.jofawtra",
    "products.cymed.integrations.zakata",
    "products.cymed.integrations.nphies",
    "products.cymed.integrations.hakeem",
    # CyMed Portals
    "products.cymed.patient_portal",
    "products.cymed.provider_portal",
    # CyMed Payments (P0-2)
    "products.cymed.payments",
    # CyMed FHIR R4 (P0-4)
    "products.cymed.fhir_r4",
    # CyMed AI CDS (P0-5)
    "products.cymed.ai_cds",
    # CyMed RCM (P0-6)
    "products.cymed.rcm",
    # CyMed Clinic gap-fill apps (P0-8)
    "products.cymed.clinic.insurance_verify",
    "products.cymed.clinic.self_checkin",
    "products.cymed.clinic.auto_coding",
    "products.cymed.clinic.referral_loop",
    "products.cymed.clinic.ecommerce",
    "products.cymed.clinic.marketing",
    # ── CyMed Pharmacy gap-fill (P0-9) ─────────────────────────────
    "products.cymed.pharmacy.ecommerce.apps.EcommerceConfig",
    "products.cymed.pharmacy.delivery.apps.DeliveryConfig",
    "products.cymed.pharmacy.pos_insurance.apps.PosInsuranceConfig",
    "products.cymed.pharmacy.loyalty.apps.LoyaltyConfig",
    "products.cymed.pharmacy.compounding.apps.CompoundingConfig",
    "products.cymed.pharmacy.robotics.apps.RoboticsConfig",
    # ── CyMed Lab gap-fill (P0-10) ─────────────────────────────────
    "products.cymed.laboratory.patient_results.apps.PatientResultsConfig",
    "products.cymed.laboratory.home_collection.apps.HomeCollectionConfig",
    "products.cymed.laboratory.online_booking.apps.OnlineBookingConfig",
    "products.cymed.laboratory.dtc_catalog.apps.DtcCatalogConfig",
    "products.cymed.laboratory.courier_tracking.apps.CourierTrackingConfig",
    # ── CyMed Imaging gap-fill (P0-11) ─────────────────────────────
    "products.cymed.imaging.patient_booking.apps.PatientBookingConfig",
    "products.cymed.imaging.patient_results.apps.PatientResultsConfig",
    "products.cymed.imaging.image_sharing.apps.ImageSharingConfig",
    "products.cymed.imaging.ai_triage.apps.AiTriageConfig",
    "products.cymed.imaging.tele_marketplace.apps.TeleMarketplaceConfig",
    "products.cymed.imaging.prep_instructions.apps.PrepInstructionsConfig",
    # ── CyMed Ecosystem Glue (P0-12) ───────────────────────────────
    "products.cymed.ecosystem.referral_routing.apps.ReferralRoutingConfig",
    "products.cymed.ecosystem.provider_directory.apps.ProviderDirectoryConfig",
    "products.cymed.ecosystem.rewards.apps.RewardsConfig",
    "products.cymed.ecosystem.analytics.apps.EcosystemAnalyticsConfig",
    "products.cymed.ecosystem.shared_capacity.apps.SharedCapacityConfig",
    "products.cymed.ecosystem.credentialing.apps.CredentialingConfig",
    # ── CyMed MRFF Program (MRFF-16..19) ───────────────────────────
    "products.cymed.mrff.ai_diagnostics.apps.AiDiagnosticsConfig",
    "products.cymed.mrff.offline_kit.apps.OfflineKitConfig",
    "products.cymed.mrff.ambient_scribe.apps.AmbientScribeConfig",
    "products.cymed.mrff.population_health.apps.PopulationHealthConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PLATFORM_APPS + PRODUCT_APPS

# ---------------------------------------------------------------------------
# MIDDLEWARE (order matters — tenant before audit)
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "platform.observability.middleware.RequestIdMiddleware",
    "platform.observability.middleware.AccessLogMiddleware",
    "platform.security.middleware.SecurityHeadersMiddleware",
    "platform.security.middleware.ClientIntegrityMiddleware",
    "platform.security.middleware.RateLimitMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Resolves the active language (session key / cookie / Accept-Language)
    # for the server-rendered portals; must sit after SessionMiddleware and
    # before CommonMiddleware. (ADR-0032: Arabic + English.)
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "shared.auth.auth_middleware.CyIdentityAuthMiddleware",
    "core.middleware.tenant.TenantIsolationMiddleware",
    # publishes request.tenant_id into the ambient tenant context so
    # TenantScopedMixin.save() can fill tenant_id when a caller forgets it
    "platform.common.middleware.TenantContextMiddleware",
    "core.middleware.branding.BrandingMiddleware",
    "core.middleware.feature_flags.FeatureFlagMiddleware",
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
                "django.template.context_processors.i18n",
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

CELERY_ENABLE_UTC = True
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_ROUTES = {
    "payments.*":       {"queue": "payments"},
    "integrations.*":   {"queue": "integrations"},
    "notifications.*":  {"queue": "notifications"},
    "ai_cds.*":         {"queue": "ai_cds"},
}

CELERY_BEAT_SCHEDULE: dict = {
    "expire-demo-tenants": {
        "task": "tenant.expire_demo_tenants",
        "schedule": 900.0,
    },
    # Drain the canonical domain-event outbox (core_domain_events) to the broker.
    "canonical-relay-domain-events": {
        "task": "canonical.relay_domain_events",
        "schedule": 30.0,
    },
}

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
# TERMINOLOGY API CONFIGURATION
# ---------------------------------------------------------------------------
ICD11_CLIENT_ID = os.environ.get("ICD11_CLIENT_ID", "")
ICD11_CLIENT_SECRET = os.environ.get("ICD11_CLIENT_SECRET", "")

FHIR_TERMINOLOGY_SERVER = os.environ.get("FHIR_TERMINOLOGY_SERVER", "https://tx.fhir.org/r4")
TERMINOLOGY_REQUESTS_TIMEOUT = int(os.environ.get("TERMINOLOGY_REQUESTS_TIMEOUT", "10"))

# ---------------------------------------------------------------------------
# JOFAWTRA (Jordan E-Invoicing)
# ---------------------------------------------------------------------------
JOFAWTRA_API_KEY = os.environ.get("JOFAWTRA_API_KEY", "")
JOFAWTRA_CLIENT_ID = os.environ.get("JOFAWTRA_CLIENT_ID", "")
JOFAWTRA_CLIENT_SECRET = os.environ.get("JOFAWTRA_CLIENT_SECRET", "")

# ---------------------------------------------------------------------------
# ZAKATA / ZATCA (Saudi E-Invoicing)
# ---------------------------------------------------------------------------
ZATCA_API_KEY = os.environ.get("ZATCA_API_KEY", "")
ZATCA_CSID = os.environ.get("ZATCA_CSID", "")
ZATCA_SECRET = os.environ.get("ZATCA_SECRET", "")

# ---------------------------------------------------------------------------
# IDENTITY — CyIdentity / Keycloak (ADR-0005)
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
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": int(os.environ.get("API_PAGE_SIZE", "25")),
    "EXCEPTION_HANDLER": "platform.api.exceptions.cybercom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "website_public_read": os.environ.get("THROTTLE_WEBSITE_READ", "600/hour"),
        "website_public_write": os.environ.get("THROTTLE_WEBSITE_WRITE", "20/hour"),
        "website_demo_request": os.environ.get("THROTTLE_DEMO_REQUEST", "5/hour"),
        "website_contact": os.environ.get("THROTTLE_CONTACT", "10/hour"),
        "website_partner_application": os.environ.get("THROTTLE_PARTNER_APP", "3/hour"),
        "website_newsletter": os.environ.get("THROTTLE_NEWSLETTER", "5/hour"),
    },
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

# Unauthenticated surfaces — the server-rendered portal shells (which render a
# public "sign in" state and gate real data on request.user_session in the
# view), the API console, and the language-switch endpoint. Consumed by
# shared.auth.auth_middleware and core.middleware.tenant.
AUTH_PUBLIC_PATHS = (
    "/",
    "/patient-portal/",
    "/patient-app/",
    "/provider-portal/",
    "/api/docs/",
    "/api/redoc/",
    "/i18n/setlang/",
)
AUTH_PUBLIC_PATH_PREFIXES = ("/api/schema/",)

# Where the portal "Sign in" button points until a full web auth flow lands.
PORTAL_LOGIN_URL = os.environ.get("PORTAL_LOGIN_URL", "/api/docs/")

# ---------------------------------------------------------------------------
# STATIC & MEDIA
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# LOGGING — structured JSON via platform.observability (ADR-0009)
# ---------------------------------------------------------------------------
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

from platform.observability.logging_config import build_logging  # noqa: E402

LOGGING = build_logging(
    service="cymed",
    env=os.environ.get("PLATFORM_ENV", os.environ.get("ENVIRONMENT", "dev")),
    level=LOG_LEVEL,
)

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

# Per-tenant field encryption (platform.common.fields.EncryptedText). 32 random
# bytes, base64. Required for PHI/PII columns. Production value from the secret
# manager / KMS; the dev default is NOT a secret.
FIELD_ENCRYPTION_KEY = os.environ.get(
    "FIELD_ENCRYPTION_KEY",
    "nA924BBgLP5/rfXoSsY4kj1m4MzPrJ1KM/W6xZfYpbA=",  # sha256("cybercom-dev-field-key-cymed") — 32 bytes
)

# PostgreSQL row-level-security enforcement (see canonical-data-model-v1.md §2.1).
# Keep false until the app DB role is confirmed non-superuser / non-BYPASSRLS;
# `manage.py apply_rls` installs the policies in deploy.
RLS_ENFORCED = os.environ.get("CYMED_RLS_ENFORCED", "0") == "1"
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
