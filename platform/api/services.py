"""
API Framework service layer. ADR-0003 / ADR-0030.
"""
import hashlib
import hmac
import json
import logging
import uuid
from datetime import timedelta
from typing import Optional

from django.utils import timezone

from .models import (
    ApiApplication, ApiCatalog, ApiClassification, ApiContract, ApiEndpoint,
    ApiKey, ApiKeyStatus, ApiPolicy, ApiRateLimit, ApiScope, ApiStatus,
    ApiSubscription, ApiUsage, ApiVersion, ApiWebhook, ApiWebhookDelivery,
    IdempotencyKey, RateLimitScope, VersionLifecycle, WebhookDeliveryStatus,
    WebhookStatus,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ApiApplicationService
# ---------------------------------------------------------------------------

class ApiApplicationService:
    """Register and manage API consumer applications."""

    def register(
        self,
        name: str,
        slug: str,
        classification: str = ApiClassification.INTERNAL,
        tenant_id=None,
        owner_email: str = "",
        callback_urls: list = None,
    ) -> ApiApplication:
        return ApiApplication.objects.create(
            name=name,
            slug=slug,
            classification=classification,
            tenant_id=tenant_id,
            owner_email=owner_email,
            callback_urls=callback_urls or [],
        )

    def suspend(self, app: ApiApplication) -> None:
        app.suspend()

    def activate(self, app: ApiApplication) -> None:
        app.activate()


# ---------------------------------------------------------------------------
# ApiKeyService
# ---------------------------------------------------------------------------

class ApiKeyService:
    """Generate, rotate, and revoke API keys."""

    def generate(
        self,
        application: ApiApplication,
        name: str,
        scopes: list = None,
        tenant_id=None,
        created_by: str = "",
        expires_in_days: int = None,
    ) -> tuple[ApiKey, str]:
        expires_at = timezone.now() + timedelta(days=expires_in_days) if expires_in_days else None
        return ApiKey.generate(
            application=application, name=name, scopes=scopes or [],
            tenant_id=tenant_id, created_by=created_by, expires_at=expires_at,
        )

    def revoke(self, key: ApiKey, revoked_by: str = "") -> None:
        key.revoke(revoked_by=revoked_by)

    def verify(self, raw_key: str) -> Optional[ApiKey]:
        if not raw_key or not raw_key.startswith("ck_"):
            return None
        prefix = raw_key[:12]
        try:
            key = ApiKey.objects.get(key_prefix=prefix, status=ApiKeyStatus.ACTIVE)
        except ApiKey.DoesNotExist:
            return None
        if not key.verify(raw_key):
            return None
        if not key.is_valid:
            return None
        key.last_used_at = timezone.now()
        key.save(update_fields=["last_used_at"])
        return key

    def rotate(self, old_key: ApiKey, created_by: str = "") -> tuple[ApiKey, str]:
        new_key, raw = ApiKey.generate(
            application=old_key.application,
            name=f"{old_key.name} (rotated)",
            scopes=old_key.scopes,
            tenant_id=old_key.tenant_id,
            created_by=created_by,
            expires_at=old_key.expires_at,
        )
        old_key.revoke(revoked_by=created_by)
        return new_key, raw


# ---------------------------------------------------------------------------
# ApiCatalogService
# ---------------------------------------------------------------------------

class ApiCatalogService:
    """Manage the API catalog registry."""

    def register(
        self,
        name: str,
        slug: str,
        classification: str,
        base_path: str,
        owner_team: str = "",
        description: str = "",
        fhir_resource: str = "",
    ) -> ApiCatalog:
        version = ApiVersion.objects.create(
            major=1, minor=0, patch=0, lifecycle=VersionLifecycle.STABLE, is_current=True
        ) if not ApiVersion.objects.exists() else ApiVersion.objects.filter(is_current=True).first()
        return ApiCatalog.objects.create(
            name=name, slug=slug, classification=classification,
            base_path=base_path, owner_team=owner_team, description=description,
            fhir_resource=fhir_resource, current_version=version,
        )

    def publish(self, catalog: ApiCatalog) -> None:
        catalog.publish()

    def deprecate(self, catalog: ApiCatalog) -> None:
        catalog.deprecate()

    def add_scope(self, catalog: ApiCatalog, name: str, description: str, is_sensitive: bool = False) -> ApiScope:
        return ApiScope.objects.create(
            catalog=catalog, name=name, description=description, is_sensitive=is_sensitive
        )

    def add_endpoint(
        self, catalog: ApiCatalog, path: str, method: str, operation_id: str, required_scopes: list = None
    ) -> ApiEndpoint:
        return ApiEndpoint.objects.create(
            catalog=catalog, path=path, method=method,
            operation_id=operation_id, required_scopes=required_scopes or [],
        )


# ---------------------------------------------------------------------------
# ApiSubscriptionService
# ---------------------------------------------------------------------------

class ApiSubscriptionService:
    """Approve and manage application-to-catalog subscriptions."""

    def subscribe(
        self,
        application: ApiApplication,
        catalog: ApiCatalog,
        approved_scopes: list = None,
        approved_by: str = "",
    ) -> ApiSubscription:
        sub, created = ApiSubscription.objects.get_or_create(
            application=application,
            catalog=catalog,
            defaults={
                "approved_scopes": approved_scopes or [],
                "approved_by": approved_by,
                "approved_at": timezone.now(),
                "status": ApiStatus.ACTIVE,
            },
        )
        if not created:
            sub.status = ApiStatus.ACTIVE
            sub.approved_scopes = approved_scopes or sub.approved_scopes
            sub.approved_by = approved_by
            sub.approved_at = timezone.now()
            sub.save(update_fields=["status", "approved_scopes", "approved_by", "approved_at", "updated_at"])
        return sub

    def has_scope(self, application: ApiApplication, catalog: ApiCatalog, scope: str) -> bool:
        try:
            sub = ApiSubscription.objects.get(application=application, catalog=catalog)
            return sub.is_active and scope in sub.approved_scopes
        except ApiSubscription.DoesNotExist:
            return False


# ---------------------------------------------------------------------------
# ApiVersionService
# ---------------------------------------------------------------------------

class ApiVersionService:
    """Manage semantic versions and deprecation per ADR-0030 S3.4."""

    def create(self, major: int, minor: int, patch: int, release_notes: str = "") -> ApiVersion:
        v = ApiVersion.objects.create(
            major=major, minor=minor, patch=patch, release_notes=release_notes
        )
        return v

    def set_current(self, version: ApiVersion) -> None:
        ApiVersion.objects.filter(is_current=True).update(is_current=False)
        version.is_current = True
        version.save(update_fields=["is_current"])

    def deprecate(self, version: ApiVersion, sunset_days: int = 180) -> None:
        sunset_at = timezone.now() + timedelta(days=sunset_days)
        version.deprecate(sunset_at=sunset_at)

    def get_deprecation_headers(self, version: ApiVersion) -> dict:
        headers = {}
        if version.deprecated_at:
            headers["Deprecation"] = version.deprecated_at.strftime("@%Y-%m-%d")
        if version.sunset_at:
            headers["Sunset"] = version.sunset_at.strftime("@%Y-%m-%d")
        return headers


# ---------------------------------------------------------------------------
# WebhookService
# ---------------------------------------------------------------------------

class WebhookService:
    """Register webhooks, dispatch events, track deliveries."""

    def register(
        self,
        application: ApiApplication,
        name: str,
        target_url: str,
        events: list,
        tenant_id=None,
        headers: dict = None,
    ) -> ApiWebhook:
        return ApiWebhook.create_with_secret(
            application=application, name=name, target_url=target_url,
            events=events, tenant_id=tenant_id, headers=headers or {},
        )

    def dispatch(self, event_type: str, payload: dict, tenant_id=None) -> list[ApiWebhookDelivery]:
        webhooks = ApiWebhook.objects.filter(
            status=WebhookStatus.ACTIVE,
            tenant_id=tenant_id,
        )
        deliveries = []
        for wh in webhooks:
            if not wh.events:
                continue
            if event_type not in wh.events and "*" not in wh.events:
                continue
            payload_str = json.dumps(payload)
            sig = wh.compute_signature(payload_str)
            delivery = ApiWebhookDelivery.objects.create(
                webhook=wh,
                event_type=event_type,
                payload=payload,
                max_attempts=wh.max_retries,
                signature=sig,
            )
            deliveries.append(delivery)
        return deliveries

    def verify_signature(self, webhook: ApiWebhook, payload: str, signature: str) -> bool:
        expected = webhook.compute_signature(payload)
        return hmac.compare_digest(expected, signature)

    def simulate_delivery(self, delivery: ApiWebhookDelivery, success: bool = True) -> None:
        if success:
            delivery.mark_delivered(response_code=200, response_body='{"ok":true}')
            wh = delivery.webhook
            wh.last_delivery_at = timezone.now()
            wh.last_delivery_status = "delivered"
            wh.failure_count = 0
            wh.save(update_fields=["last_delivery_at", "last_delivery_status", "failure_count", "updated_at"])
        else:
            delivery.mark_failed("Connection refused", response_code=None)
            wh = delivery.webhook
            wh.failure_count += 1
            wh.save(update_fields=["failure_count", "updated_at"])

    def pause(self, webhook: ApiWebhook) -> None:
        webhook.pause()

    def disable(self, webhook: ApiWebhook) -> None:
        webhook.disable()


# ---------------------------------------------------------------------------
# ApiContractService
# ---------------------------------------------------------------------------

class ApiContractService:
    """Contract testing and schema drift detection. ADR-0003 S7.3."""

    def register(
        self,
        catalog: ApiCatalog,
        version: ApiVersion,
        consumer_name: str,
        schema: dict,
    ) -> ApiContract:
        schema_hash = hashlib.sha256(str(sorted(schema.items())).encode()).hexdigest()
        return ApiContract.objects.create(
            catalog=catalog,
            version=version,
            consumer_name=consumer_name,
            schema_snapshot=schema,
            schema_hash=schema_hash,
        )

    def validate(self, contract: ApiContract, current_schema: dict) -> bool:
        return contract.validate_against(current_schema)

    def validate_all(self, catalog: ApiCatalog) -> list:
        contracts = ApiContract.objects.filter(catalog=catalog)
        results = []
        for contract in contracts:
            is_valid = contract.validate_against(catalog.openapi_schema)
            results.append({
                "contract": str(contract.id),
                "consumer": contract.consumer_name,
                "valid": is_valid,
                "errors": contract.validation_errors,
            })
        return results


# ---------------------------------------------------------------------------
# ApiUsageService
# ---------------------------------------------------------------------------

class ApiUsageService:
    """Usage analytics and quota tracking."""

    def record(
        self,
        endpoint_path: str,
        method: str,
        status_code: int,
        tenant_id=None,
        application: ApiApplication = None,
        latency_ms: int = 0,
        correlation_id: str = "",
    ) -> ApiUsage:
        return ApiUsage.objects.create(
            endpoint_path=endpoint_path,
            http_method=method,
            status_code=status_code,
            tenant_id=tenant_id,
            application=application,
            latency_ms=latency_ms,
            correlation_id=correlation_id,
            is_error=status_code >= 400,
        )

    def get_tenant_summary(self, tenant_id, days: int = 30) -> dict:
        from django.db.models import Count, Avg
        since = timezone.now() - timedelta(days=days)
        qs = ApiUsage.objects.filter(tenant_id=tenant_id, timestamp__gte=since)
        return qs.aggregate(
            total_requests=Count("id"),
            avg_latency=Avg("latency_ms"),
            error_count=Count("id", filter=__import__("django.db.models", fromlist=["Q"]).Q(is_error=True)),
        )


# ---------------------------------------------------------------------------
# ApiRateLimitService
# ---------------------------------------------------------------------------

class ApiRateLimitService:
    """Manage rate limit configurations per catalog/application/tenant."""

    def set_tenant_limit(
        self, tenant_id, requests_per_minute: int = 60, requests_per_day: int = 86400, burst_size: int = 20
    ) -> ApiRateLimit:
        obj, _ = ApiRateLimit.objects.update_or_create(
            tenant_id=tenant_id, scope=RateLimitScope.TENANT, catalog=None, application=None,
            defaults={
                "requests_per_minute": requests_per_minute,
                "requests_per_day": requests_per_day,
                "burst_size": burst_size,
            },
        )
        return obj


# ---------------------------------------------------------------------------
# FHIRService — FHIR R4 resource helpers
# ---------------------------------------------------------------------------

class FHIRService:
    """
    FHIR R4 / R5 resource builder.
    In production, delegates to Go FHIR gateway (ADR-0034 S4.2).
    In this Django layer, provides the REST interface and audit trail.
    """
    SUPPORTED_RESOURCES = [
        "Patient", "Encounter", "Practitioner", "Observation",
        "MedicationRequest", "Appointment", "CarePlan", "DiagnosticReport",
    ]
    SUPPORTED_VERSIONS = ["R4", "R5"]

    def build_patient(self, patient_id: str, tenant_id=None) -> dict:
        return {
            "resourceType": "Patient",
            "id": patient_id,
            "meta": {"versionId": "1", "lastUpdated": timezone.now().isoformat()},
            "identifier": [{"system": "urn:cybercom:patient", "value": patient_id}],
            "active": True,
        }

    def build_observation(self, obs_id: str, patient_id: str, code: str, value: str) -> dict:
        return {
            "resourceType": "Observation",
            "id": obs_id,
            "status": "final",
            "code": {"coding": [{"system": "http://loinc.org", "code": code}]},
            "subject": {"reference": f"Patient/{patient_id}"},
            "valueString": value,
            "effectiveDateTime": timezone.now().isoformat(),
        }

    def build_encounter(self, enc_id: str, patient_id: str, status: str = "in-progress") -> dict:
        return {
            "resourceType": "Encounter",
            "id": enc_id,
            "status": status,
            "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "IMP"},
            "subject": {"reference": f"Patient/{patient_id}"},
        }

    def build_bundle(self, resource_type: str, resources: list, total: int = None) -> dict:
        return {
            "resourceType": "Bundle",
            "id": str(uuid.uuid4()),
            "type": "searchset",
            "total": total if total is not None else len(resources),
            "entry": [{"resource": r} for r in resources],
        }

    def build_operation_outcome(self, severity: str, code: str, diagnostics: str) -> dict:
        return {
            "resourceType": "OperationOutcome",
            "issue": [{"severity": severity, "code": code, "diagnostics": diagnostics}],
        }

    def is_supported(self, resource_type: str) -> bool:
        return resource_type in self.SUPPORTED_RESOURCES


# ---------------------------------------------------------------------------
# SDKGeneratorService
# ---------------------------------------------------------------------------

class SDKGeneratorService:
    """
    Generates SDK stubs from OpenAPI schema.
    Full generation handled by openapi-generator-cli in CI.
    This service produces the spec and triggers generation config.
    """

    def generate_typescript_stub(self, catalog: ApiCatalog) -> str:
        name = catalog.slug.replace("-", "_")
        return f"""// CyberCom TypeScript SDK — {catalog.name}
// Auto-generated. Do not edit manually.
// Source: {catalog.base_path}

export interface ApiResponse<T> {{
  data: T;
  pagination?: {{ next_cursor: string | null; has_more: boolean; limit: number }};
}}

export class {name.title().replace("_", "")}Client {{
  private baseUrl: string;
  private apiKey: string;

  constructor(baseUrl: string, apiKey: string) {{
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }}

  private async request<T>(path: string, method = "GET", body?: unknown): Promise<ApiResponse<T>> {{
    const response = await fetch(`${{this.baseUrl}}${{path}}`, {{
      method,
      headers: {{
        "Authorization": `Bearer ${{this.apiKey}}`,
        "Content-Type": "application/json",
        "X-API-Version": "1.0.0",
      }},
      body: body ? JSON.stringify(body) : undefined,
    }});
    if (!response.ok) {{
      const err = await response.json();
      throw new Error(err.detail || "API error");
    }}
    return response.json();
  }}
}}
"""

    def generate_python_stub(self, catalog: ApiCatalog) -> str:
        name = catalog.slug.replace("-", "_")
        return f'''"""
CyberCom Python SDK — {catalog.name}
Auto-generated. Do not edit manually.
Source: {catalog.base_path}
"""
import requests
from typing import Any, Optional

class {name.title().replace("_", "")}Client:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({{
            "Authorization": f"Bearer {{api_key}}",
            "Content-Type": "application/json",
            "X-API-Version": "1.0.0",
        }})

    def _request(self, method: str, path: str, **kwargs) -> Any:
        r = self.session.request(method, f"{{self.base_url}}{{path}}", **kwargs)
        r.raise_for_status()
        return r.json()
'''

    def get_openapi_spec(self, catalog: ApiCatalog) -> dict:
        endpoints = list(catalog.endpoints.all())
        paths = {}
        for ep in endpoints:
            if ep.path not in paths:
                paths[ep.path] = {}
            paths[ep.path][ep.method.lower()] = {
                "operationId": ep.operation_id,
                "summary": ep.summary,
                "security": [{"bearerAuth": ep.required_scopes}] if ep.requires_auth else [],
                "responses": {"200": {"description": "Success"}, "default": {"description": "Error"}},
            }

        return {
            "openapi": "3.1.0",
            "info": {
                "title": catalog.name,
                "version": catalog.current_version.version_string if catalog.current_version else "v1.0.0",
                "description": catalog.description,
            },
            "servers": [{"url": catalog.base_path}],
            "paths": paths,
            "components": {
                "securitySchemes": {
                    "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
                }
            },
        }


# ---------------------------------------------------------------------------
# ApiMetrics
# ---------------------------------------------------------------------------

class ApiMetrics:
    """Prometheus metrics for the API framework."""

    def render_prometheus(self) -> str:
        total = ApiUsage.objects.count()
        errors = ApiUsage.objects.filter(is_error=True).count()
        rate_limited = ApiUsage.objects.filter(is_rate_limited=True).count()
        active_keys = ApiKey.objects.filter(status="active").count()
        active_webhooks = ApiWebhook.objects.filter(status="active").count()
        dead_deliveries = ApiWebhookDelivery.objects.filter(status=WebhookDeliveryStatus.DEAD).count()
        active_apps = ApiApplication.objects.filter(status="active").count()
        active_catalogs = ApiCatalog.objects.filter(status="active").count()

        lines = [
            "# HELP cybercom_api_requests_total Total API requests",
            "# TYPE cybercom_api_requests_total counter",
            f"cybercom_api_requests_total {total}",
            "# HELP cybercom_api_errors_total Total API errors",
            "# TYPE cybercom_api_errors_total counter",
            f"cybercom_api_errors_total {errors}",
            "# HELP cybercom_api_rate_limited_total Rate-limited requests",
            "# TYPE cybercom_api_rate_limited_total counter",
            f"cybercom_api_rate_limited_total {rate_limited}",
            "# HELP cybercom_api_keys_active Active API keys",
            "# TYPE cybercom_api_keys_active gauge",
            f"cybercom_api_keys_active {active_keys}",
            "# HELP cybercom_api_webhooks_active Active webhooks",
            "# TYPE cybercom_api_webhooks_active gauge",
            f"cybercom_api_webhooks_active {active_webhooks}",
            "# HELP cybercom_api_webhook_dead_letters Dead-letter webhook deliveries",
            "# TYPE cybercom_api_webhook_dead_letters gauge",
            f"cybercom_api_webhook_dead_letters {dead_deliveries}",
            "# HELP cybercom_api_applications_active Active API applications",
            "# TYPE cybercom_api_applications_active gauge",
            f"cybercom_api_applications_active {active_apps}",
            "# HELP cybercom_api_catalogs_active Published APIs in catalog",
            "# TYPE cybercom_api_catalogs_active gauge",
            f"cybercom_api_catalogs_active {active_catalogs}",
        ]
        return "\n".join(lines) + "\n"
