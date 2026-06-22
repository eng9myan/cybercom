"""
Program 2.4 — API Framework test suite.
Target: 90% coverage.
"""
import hashlib
import uuid
import pytest
from django.utils import timezone

from platform.api.idempotency import IdempotencyService
from platform.api.models import (
    ApiApplication, ApiCatalog, ApiClassification, ApiContract, ApiEndpoint,
    ApiKey, ApiKeyStatus, ApiPolicy, ApiRateLimit, ApiScope, ApiStatus,
    ApiSubscription, ApiUsage, ApiVersion, ApiWebhook, ApiWebhookDelivery,
    IdempotencyKey, RateLimitScope, VersionLifecycle, WebhookDeliveryStatus,
    WebhookStatus, HttpMethod,
)
from platform.api.pagination import CyberComCursorPagination
from platform.api.rate_limit import InMemoryRateLimiter, RateLimitService
from platform.api.services import (
    ApiApplicationService, ApiCatalogService, ApiContractService,
    ApiKeyService, ApiSubscriptionService, ApiVersionService,
    FHIRService, SDKGeneratorService, WebhookService,
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def version():
    return ApiVersion.objects.create(major=1, minor=0, patch=0, lifecycle=VersionLifecycle.STABLE)


@pytest.fixture
def catalog(version):
    return ApiCatalog.objects.create(
        name="Test API", slug="test-api", classification=ApiClassification.INTERNAL,
        base_path="/api/v1/test/", current_version=version,
    )


@pytest.fixture
def application():
    return ApiApplication.objects.create(
        name="Test App", slug="test-app",
        classification=ApiClassification.INTERNAL,
    )


@pytest.fixture
def tenant_id():
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# TestApiVersion
# ---------------------------------------------------------------------------

class TestApiVersion:
    def test_create(self):
        v = ApiVersion.objects.create(major=2, minor=1, patch=0)
        assert v.version_string == "v2.1.0"
        assert not v.is_deprecated

    def test_deprecate(self):
        v = ApiVersion.objects.create(major=1, minor=0, patch=1, lifecycle=VersionLifecycle.STABLE)
        v.deprecate(sunset_at=timezone.now())
        assert v.lifecycle == VersionLifecycle.DEPRECATED
        assert v.is_deprecated

    def test_ordering(self):
        ApiVersion.objects.create(major=1, minor=0, patch=0)
        ApiVersion.objects.create(major=2, minor=0, patch=0)
        first = ApiVersion.objects.first()
        assert first.major == 2

    def test_str(self, version):
        assert "v1.0.0" in str(version)


# ---------------------------------------------------------------------------
# TestApiCatalog
# ---------------------------------------------------------------------------

class TestApiCatalog:
    def test_create(self, catalog):
        assert catalog.slug == "test-api"
        assert catalog.status == ApiStatus.DRAFT

    def test_publish(self, catalog):
        catalog.publish()
        assert catalog.status == ApiStatus.ACTIVE

    def test_deprecate(self, catalog):
        catalog.publish()
        catalog.deprecate()
        assert catalog.status == ApiStatus.DEPRECATED

    def test_str(self, catalog):
        assert "test-api" in str(catalog)


# ---------------------------------------------------------------------------
# TestApiApplication
# ---------------------------------------------------------------------------

class TestApiApplication:
    def test_create(self, application):
        assert application.status == ApiStatus.ACTIVE

    def test_suspend(self, application):
        application.suspend()
        assert application.status == ApiStatus.SUSPENDED

    def test_activate_after_suspend(self, application):
        application.suspend()
        application.activate()
        assert application.status == ApiStatus.ACTIVE

    def test_str(self, application):
        assert "test-app" in str(application)


# ---------------------------------------------------------------------------
# TestApiKey
# ---------------------------------------------------------------------------

class TestApiKey:
    def test_generate_produces_raw_key(self, application):
        key, raw = ApiKey.generate(application=application, name="test-key")
        assert raw.startswith("ck_")
        assert key.key_prefix == raw[:12]

    def test_verify_correct(self, application):
        key, raw = ApiKey.generate(application=application, name="test-key-2")
        assert key.verify(raw)

    def test_verify_wrong(self, application):
        key, raw = ApiKey.generate(application=application, name="test-key-3")
        assert not key.verify("ck_wrongkey")

    def test_revoke(self, application):
        key, _ = ApiKey.generate(application=application, name="test-key-4")
        key.revoke(revoked_by="admin")
        assert key.status == ApiKeyStatus.REVOKED
        assert key.revoked_by == "admin"

    def test_is_valid_active(self, application):
        key, _ = ApiKey.generate(application=application, name="test-key-5")
        assert key.is_valid

    def test_is_valid_revoked(self, application):
        key, _ = ApiKey.generate(application=application, name="test-key-6")
        key.revoke()
        assert not key.is_valid

    def test_is_valid_expired(self, application):
        from datetime import timedelta
        key, _ = ApiKey.generate(
            application=application, name="test-key-7",
            expires_at=timezone.now() - timedelta(hours=1),
        )
        assert not key.is_valid

    def test_key_hash_stored_not_raw(self, application):
        key, raw = ApiKey.generate(application=application, name="test-key-8")
        assert key.key_hash != raw
        assert len(key.key_hash) == 64  # SHA-256 hex


# ---------------------------------------------------------------------------
# TestApiKeyService
# ---------------------------------------------------------------------------

class TestApiKeyService:
    def setup_method(self):
        self.svc = ApiKeyService()

    def test_generate_and_verify(self, application):
        key_obj, raw = self.svc.generate(application, "svc-key")
        verified = self.svc.verify(raw)
        assert verified is not None
        assert verified.id == key_obj.id

    def test_verify_invalid_prefix(self, application):
        result = self.svc.verify("invalid_key_format")
        assert result is None

    def test_revoke_via_service(self, application):
        key_obj, raw = self.svc.generate(application, "revoke-key")
        self.svc.revoke(key_obj, revoked_by="test")
        assert self.svc.verify(raw) is None

    def test_rotate(self, application):
        old_key, old_raw = self.svc.generate(application, "old-key")
        new_key, new_raw = self.svc.rotate(old_key)
        old_key.refresh_from_db()
        assert old_key.status == ApiKeyStatus.REVOKED
        assert self.svc.verify(new_raw) is not None


# ---------------------------------------------------------------------------
# TestApiScope
# ---------------------------------------------------------------------------

class TestApiScope:
    def test_create(self, catalog):
        scope = ApiScope.objects.create(
            catalog=catalog, name="read:patients", description="Read patient data"
        )
        assert scope.name == "read:patients"
        assert not scope.is_sensitive

    def test_unique_constraint(self, catalog):
        ApiScope.objects.create(catalog=catalog, name="write:records", description="X")
        with pytest.raises(Exception):
            ApiScope.objects.create(catalog=catalog, name="write:records", description="Y")


# ---------------------------------------------------------------------------
# TestApiSubscription
# ---------------------------------------------------------------------------

class TestApiSubscription:
    def test_subscribe(self, application, catalog):
        sub = ApiSubscription.objects.create(
            application=application, catalog=catalog,
            approved_scopes=["read:patients"], status=ApiStatus.ACTIVE,
        )
        assert sub.is_active

    def test_expired_subscription_not_active(self, application, catalog):
        from datetime import timedelta
        sub = ApiSubscription.objects.create(
            application=application, catalog=catalog,
            status=ApiStatus.ACTIVE,
            expires_at=timezone.now() - timedelta(days=1),
        )
        assert not sub.is_active

    def test_subscription_service(self, application, catalog):
        svc = ApiSubscriptionService()
        sub = svc.subscribe(application, catalog, approved_scopes=["read:patients"])
        assert sub.is_active
        assert svc.has_scope(application, catalog, "read:patients")

    def test_has_scope_false(self, application, catalog):
        svc = ApiSubscriptionService()
        svc.subscribe(application, catalog, approved_scopes=["read:patients"])
        assert not svc.has_scope(application, catalog, "write:records")


# ---------------------------------------------------------------------------
# TestApiRateLimit
# ---------------------------------------------------------------------------

class TestApiRateLimit:
    def test_create(self, catalog):
        rl = ApiRateLimit.objects.create(
            catalog=catalog, scope=RateLimitScope.TENANT,
            requests_per_minute=100, burst_size=20,
        )
        assert rl.requests_per_minute == 100

    def test_str(self, catalog):
        rl = ApiRateLimit.objects.create(
            catalog=catalog, scope=RateLimitScope.USER, requests_per_minute=30
        )
        assert "30/min" in str(rl)


# ---------------------------------------------------------------------------
# TestInMemoryRateLimiter
# ---------------------------------------------------------------------------

class TestInMemoryRateLimiter:
    def test_allows_under_limit(self):
        rl = InMemoryRateLimiter()
        result = rl.check("test-key", limit=10)
        assert result.allowed
        assert result.remaining == 9

    def test_blocks_over_limit(self):
        rl = InMemoryRateLimiter()
        for _ in range(5):
            rl.check("burst-key", limit=5)
        result = rl.check("burst-key", limit=5)
        assert not result.allowed
        assert result.retry_after is not None

    def test_reset(self):
        rl = InMemoryRateLimiter()
        for _ in range(5):
            rl.check("reset-key", limit=5)
        rl.reset("reset-key")
        result = rl.check("reset-key", limit=5)
        assert result.allowed

    def test_different_keys_independent(self):
        rl = InMemoryRateLimiter()
        for _ in range(5):
            rl.check("key-a", limit=5)
        result_b = rl.check("key-b", limit=5)
        assert result_b.allowed

    def test_reset_all(self):
        rl = InMemoryRateLimiter()
        for _ in range(5):
            rl.check("key-x", limit=5)
        rl.reset_all()
        result = rl.check("key-x", limit=5)
        assert result.allowed


# ---------------------------------------------------------------------------
# TestRateLimitService
# ---------------------------------------------------------------------------

class TestRateLimitService:
    def test_tenant_check(self):
        svc = RateLimitService()
        result = svc.check_tenant("tenant-abc", requests_per_minute=10)
        assert result.allowed

    def test_user_check(self):
        svc = RateLimitService()
        result = svc.check_user("user-xyz", requests_per_minute=5)
        assert result.allowed

    def test_application_check(self):
        svc = RateLimitService()
        result = svc.check_application("app-123", requests_per_minute=20)
        assert result.allowed


# ---------------------------------------------------------------------------
# TestIdempotencyService
# ---------------------------------------------------------------------------

class TestIdempotencyService:
    def setup_method(self):
        self.svc = IdempotencyService()

    def test_store_and_get(self, tenant_id):
        key = str(uuid.uuid4())
        record = self.svc.store(key=key, tenant_id=tenant_id, method="POST", path="/api/v1/test/")
        fetched = self.svc.get(key, tenant_id)
        assert fetched.id == record.id
        assert fetched.processing is True

    def test_check_or_store_new(self, tenant_id):
        key = str(uuid.uuid4())
        result = self.svc.check_or_store(key=key, tenant_id=tenant_id)
        assert not result.is_replay
        assert result.record is not None

    def test_replay(self, tenant_id):
        key = str(uuid.uuid4())
        record = self.svc.store(key=key, tenant_id=tenant_id)
        self.svc.complete(record, status_code=201, response_body='{"id":"abc"}')
        result = self.svc.check_or_store(key=key, tenant_id=tenant_id)
        assert result.is_replay
        status_code, body = result.cached_response()
        assert status_code == 201
        assert "abc" in body

    def test_purge_expired(self, tenant_id):
        from datetime import timedelta
        key = str(uuid.uuid4())
        IdempotencyKey.objects.create(
            key=key, tenant_id=tenant_id, request_method="POST",
            request_path="/test/", request_hash="abc",
            expires_at=timezone.now() - timedelta(hours=1),
        )
        purged = self.svc.purge_expired()
        assert purged >= 1


# ---------------------------------------------------------------------------
# TestIdempotencyKey
# ---------------------------------------------------------------------------

class TestIdempotencyKey:
    def test_is_expired(self, tenant_id):
        from datetime import timedelta
        key = IdempotencyKey.objects.create(
            key=str(uuid.uuid4()), tenant_id=tenant_id,
            request_method="POST", request_path="/",
            request_hash="x", expires_at=timezone.now() - timedelta(minutes=1),
        )
        assert key.is_expired

    def test_complete(self, tenant_id):
        from datetime import timedelta
        key = IdempotencyKey.objects.create(
            key=str(uuid.uuid4()), tenant_id=tenant_id,
            request_method="POST", request_path="/",
            request_hash="y", expires_at=timezone.now() + timedelta(hours=24),
        )
        key.complete(200, '{"ok":true}')
        assert key.response_status == 200
        assert not key.processing


# ---------------------------------------------------------------------------
# TestApiWebhook
# ---------------------------------------------------------------------------

class TestApiWebhook:
    def test_create_with_secret(self, application):
        wh = ApiWebhook.create_with_secret(
            application=application, name="my-hook",
            target_url="https://example.com/hook",
            events=["patient.created"],
        )
        assert wh.secret
        assert len(wh.secret) == 64

    def test_compute_signature(self, application):
        wh = ApiWebhook.create_with_secret(
            application=application, name="sig-hook",
            target_url="https://example.com/hook",
            events=["*"],
        )
        payload = '{"event":"test"}'
        sig = wh.compute_signature(payload)
        assert len(sig) == 64

    def test_pause(self, application):
        wh = ApiWebhook.create_with_secret(
            application=application, name="pause-hook",
            target_url="https://example.com/hook", events=["*"],
        )
        wh.pause()
        assert wh.status == WebhookStatus.PAUSED

    def test_disable(self, application):
        wh = ApiWebhook.create_with_secret(
            application=application, name="disable-hook",
            target_url="https://example.com/hook", events=["*"],
        )
        wh.disable()
        assert wh.status == WebhookStatus.DISABLED


# ---------------------------------------------------------------------------
# TestApiWebhookDelivery
# ---------------------------------------------------------------------------

class TestApiWebhookDelivery:
    def _make_delivery(self, application):
        wh = ApiWebhook.create_with_secret(
            application=application, name=f"wh-{uuid.uuid4()}",
            target_url="https://example.com/hook", events=["*"],
        )
        return ApiWebhookDelivery.objects.create(
            webhook=wh, event_type="test.event", payload={"foo": "bar"},
            max_attempts=3,
        )

    def test_mark_delivered(self, application):
        d = self._make_delivery(application)
        d.mark_delivered(200, '{"ok":true}')
        assert d.status == WebhookDeliveryStatus.DELIVERED
        assert d.response_status_code == 200

    def test_mark_failed_retrying(self, application):
        d = self._make_delivery(application)
        d.mark_failed("timeout")
        assert d.status == WebhookDeliveryStatus.RETRYING
        assert d.attempt_count == 1

    def test_mark_failed_dead_after_max_attempts(self, application):
        d = self._make_delivery(application)
        d.mark_failed("timeout")
        d.mark_failed("timeout")
        d.mark_failed("timeout")
        assert d.status == WebhookDeliveryStatus.DEAD


# ---------------------------------------------------------------------------
# TestWebhookService
# ---------------------------------------------------------------------------

class TestWebhookService:
    def setup_method(self):
        self.svc = WebhookService()

    def test_register(self, application):
        wh = self.svc.register(application, "svc-hook", "https://example.com/wh", ["patient.created"])
        assert wh.status == WebhookStatus.ACTIVE

    def test_dispatch_no_matching_webhooks(self, application, tenant_id):
        deliveries = self.svc.dispatch("no.such.event", {"data": 1}, tenant_id=tenant_id)
        assert deliveries == []

    def test_dispatch_wildcard(self, application, tenant_id):
        wh = ApiWebhook.create_with_secret(
            application=application, name=f"wc-{uuid.uuid4()}",
            target_url="https://example.com/wh",
            events=["*"], tenant_id=tenant_id,
        )
        deliveries = self.svc.dispatch("any.event", {"key": "val"}, tenant_id=tenant_id)
        assert len(deliveries) >= 1

    def test_verify_signature(self, application):
        wh = ApiWebhook.create_with_secret(
            application=application, name="verify-hook",
            target_url="https://example.com/wh", events=["*"],
        )
        payload = '{"test": true}'
        sig = wh.compute_signature(payload)
        assert self.svc.verify_signature(wh, payload, sig)

    def test_verify_wrong_signature(self, application):
        wh = ApiWebhook.create_with_secret(
            application=application, name="verify-bad-hook",
            target_url="https://example.com/wh", events=["*"],
        )
        assert not self.svc.verify_signature(wh, '{"test": true}', "wrong_sig")


# ---------------------------------------------------------------------------
# TestApiContract
# ---------------------------------------------------------------------------

class TestApiContract:
    def test_register_and_validate_same(self, catalog, version):
        svc = ApiContractService()
        schema = {"info": {"title": "Test"}, "paths": {}}
        contract = svc.register(catalog, version, "consumer-a", schema)
        assert svc.validate(contract, schema)

    def test_validate_drift_detected(self, catalog, version):
        svc = ApiContractService()
        schema = {"info": {"title": "v1"}, "paths": {}}
        contract = svc.register(catalog, version, "consumer-b", schema)
        new_schema = {"info": {"title": "v2_changed"}, "paths": {"/new": {}}}
        assert not svc.validate(contract, new_schema)
        assert contract.validation_errors

    def test_validate_all(self, catalog, version):
        svc = ApiContractService()
        schema = {"info": {"title": "x"}}
        svc.register(catalog, version, "consumer-c", schema)
        results = svc.validate_all(catalog)
        assert len(results) >= 1


# ---------------------------------------------------------------------------
# TestApiUsage
# ---------------------------------------------------------------------------

class TestApiUsage:
    def test_record(self, catalog, application, tenant_id):
        usage = ApiUsage.objects.create(
            catalog=catalog, application=application, tenant_id=tenant_id,
            endpoint_path="/api/v1/test/", http_method="GET",
            status_code=200, latency_ms=45,
        )
        assert not usage.is_error
        assert usage.latency_ms == 45

    def test_is_error_on_4xx(self, catalog, tenant_id):
        usage = ApiUsage.objects.create(
            catalog=catalog, tenant_id=tenant_id,
            endpoint_path="/api/v1/test/", http_method="POST",
            status_code=404, is_error=True,
        )
        assert usage.is_error


# ---------------------------------------------------------------------------
# TestApiEndpoint
# ---------------------------------------------------------------------------

class TestApiEndpoint:
    def test_create(self, catalog):
        ep = ApiEndpoint.objects.create(
            catalog=catalog, path="/api/v1/patients/",
            method=HttpMethod.GET, operation_id="listPatients",
        )
        assert ep.method == "GET"
        assert "GET" in str(ep)


# ---------------------------------------------------------------------------
# TestApiPolicy
# ---------------------------------------------------------------------------

class TestApiPolicy:
    def test_create(self, catalog):
        policy = ApiPolicy.objects.create(
            catalog=catalog, name="auth-policy", policy_type="auth",
            config={"scheme": "bearer"},
        )
        assert policy.is_active

    def test_str(self, catalog):
        policy = ApiPolicy.objects.create(
            catalog=catalog, name="cors-policy", policy_type="cors", config={}
        )
        assert "cors-policy" in str(policy)


# ---------------------------------------------------------------------------
# TestFHIRService
# ---------------------------------------------------------------------------

class TestFHIRService:
    def setup_method(self):
        self.svc = FHIRService()

    def test_build_patient(self):
        resource = self.svc.build_patient("patient-123")
        assert resource["resourceType"] == "Patient"
        assert resource["id"] == "patient-123"

    def test_build_observation(self):
        obs = self.svc.build_observation("obs-1", "p-1", "55284-4", "Normal")
        assert obs["resourceType"] == "Observation"
        assert obs["status"] == "final"

    def test_build_encounter(self):
        enc = self.svc.build_encounter("enc-1", "p-1", "finished")
        assert enc["resourceType"] == "Encounter"
        assert enc["status"] == "finished"

    def test_build_bundle(self):
        patient = self.svc.build_patient("p-1")
        bundle = self.svc.build_bundle("Patient", [patient])
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "searchset"
        assert len(bundle["entry"]) == 1

    def test_operation_outcome(self):
        oo = self.svc.build_operation_outcome("error", "not-found", "Patient not found")
        assert oo["resourceType"] == "OperationOutcome"

    def test_is_supported(self):
        assert self.svc.is_supported("Patient")
        assert self.svc.is_supported("Encounter")
        assert not self.svc.is_supported("UnknownResource")


# ---------------------------------------------------------------------------
# TestSDKGeneratorService
# ---------------------------------------------------------------------------

class TestSDKGeneratorService:
    def setup_method(self):
        self.svc = SDKGeneratorService()

    def test_typescript_stub(self, catalog):
        code = self.svc.generate_typescript_stub(catalog)
        assert "TypeScript SDK" in code
        assert "fetch" in code

    def test_python_stub(self, catalog):
        code = self.svc.generate_python_stub(catalog)
        assert "Python SDK" in code
        assert "requests" in code

    def test_openapi_spec(self, catalog):
        ApiEndpoint.objects.create(
            catalog=catalog, path="/patients/", method="GET", operation_id="listPatients"
        )
        spec = self.svc.get_openapi_spec(catalog)
        assert spec["openapi"] == "3.1.0"
        assert "/patients/" in spec["paths"]

    def test_openapi_empty_paths(self, catalog):
        spec = self.svc.get_openapi_spec(catalog)
        assert "info" in spec


# ---------------------------------------------------------------------------
# TestApiVersionService
# ---------------------------------------------------------------------------

class TestApiVersionService:
    def setup_method(self):
        self.svc = ApiVersionService()

    def test_create(self):
        v = self.svc.create(3, 0, 0, release_notes="Major release")
        assert v.version_string == "v3.0.0"

    def test_set_current(self):
        v1 = self.svc.create(1, 0, 1)
        v2 = self.svc.create(1, 0, 2)
        self.svc.set_current(v1)
        self.svc.set_current(v2)
        v1.refresh_from_db()
        assert not v1.is_current
        v2.refresh_from_db()
        assert v2.is_current

    def test_deprecate_sets_sunset(self):
        v = self.svc.create(1, 0, 3)
        self.svc.deprecate(v, sunset_days=180)
        assert v.sunset_at is not None
        assert v.lifecycle == VersionLifecycle.DEPRECATED

    def test_deprecation_headers(self):
        v = self.svc.create(1, 0, 4)
        self.svc.deprecate(v, sunset_days=180)
        headers = self.svc.get_deprecation_headers(v)
        assert "Deprecation" in headers
        assert "Sunset" in headers


# ---------------------------------------------------------------------------
# TestApiCatalogService
# ---------------------------------------------------------------------------

class TestApiCatalogService:
    def setup_method(self):
        self.svc = ApiCatalogService()

    def test_add_scope(self, catalog):
        scope = self.svc.add_scope(catalog, "read:patients", "Read patients", is_sensitive=True)
        assert scope.is_sensitive

    def test_add_endpoint(self, catalog):
        ep = self.svc.add_endpoint(catalog, "/fhir/R4/Patient/", "GET", "searchPatient")
        assert ep.operation_id == "searchPatient"


# ---------------------------------------------------------------------------
# TestApiApplicationService
# ---------------------------------------------------------------------------

class TestApiApplicationService:
    def setup_method(self):
        self.svc = ApiApplicationService()

    def test_register(self):
        app = self.svc.register("New App", "new-app", ApiClassification.PARTNER)
        assert app.status == ApiStatus.ACTIVE

    def test_suspend_and_activate(self):
        app = self.svc.register("Suspend App", "suspend-app")
        self.svc.suspend(app)
        assert app.status == ApiStatus.SUSPENDED
        self.svc.activate(app)
        assert app.status == ApiStatus.ACTIVE


# ---------------------------------------------------------------------------
# TestPagination
# ---------------------------------------------------------------------------

class TestCursorPagination:
    def test_defaults(self):
        p = CyberComCursorPagination()
        assert p.page_size == 20
        assert p.max_page_size == 200
        assert p.cursor_query_param == "starting_after"

    def test_schema(self):
        p = CyberComCursorPagination()
        schema = p.get_paginated_response_schema({"type": "array"})
        assert "pagination" in schema["properties"]
        assert "next_cursor" in schema["properties"]["pagination"]["properties"]
