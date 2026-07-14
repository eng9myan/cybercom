"""
API Framework ViewSets + FHIR endpoints.
ADR-0003 REST + OpenAPI 3.1. ADR-0030 governance.
"""

import logging

from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .idempotency import IdempotencyService
from .models import (
    ApiApplication,
    ApiCatalog,
    ApiContract,
    ApiKey,
    ApiPolicy,
    ApiRateLimit,
    ApiSubscription,
    ApiUsage,
    ApiVersion,
    ApiWebhook,
    IdempotencyKey,
)
from .pagination import ApiUsageCursorPagination, CyberComCursorPagination, FHIRBundlePagination
from .permissions import CanManageWebhooks, IsApiAdmin, IsApiOwner, ReadOnlyOrApiAdmin
from .serializers import (
    ApiApplicationSerializer,
    ApiCatalogSerializer,
    ApiContractSerializer,
    ApiContractValidateSerializer,
    ApiEndpointSerializer,
    ApiKeyCreateSerializer,
    ApiKeyRevokeSerializer,
    ApiKeySerializer,
    ApiPolicySerializer,
    ApiRateLimitSerializer,
    ApiScopeSerializer,
    ApiSubscriptionSerializer,
    ApiUsageSerializer,
    ApiVersionSerializer,
    ApiWebhookDeliverySerializer,
    ApiWebhookSerializer,
    IdempotencyKeySerializer,
    SDKGenerateSerializer,
    WebhookDispatchSerializer,
)
from .services import (
    ApiApplicationService,
    ApiCatalogService,
    ApiContractService,
    ApiKeyService,
    ApiSubscriptionService,
    ApiVersionService,
    FHIRService,
    SDKGeneratorService,
    WebhookService,
)

log = logging.getLogger(__name__)

_app_svc = ApiApplicationService()
_key_svc = ApiKeyService()
_catalog_svc = ApiCatalogService()
_sub_svc = ApiSubscriptionService()
_ver_svc = ApiVersionService()
_webhook_svc = WebhookService()
_contract_svc = ApiContractService()
_fhir_svc = FHIRService()
_sdk_svc = SDKGeneratorService()
_idempotency_svc = IdempotencyService()


# ---------------------------------------------------------------------------
# ApiVersionViewSet
# ---------------------------------------------------------------------------


class ApiVersionViewSet(viewsets.ModelViewSet):
    queryset = ApiVersion.objects.all().order_by("-major", "-minor", "-patch")
    serializer_class = ApiVersionSerializer
    permission_classes = [IsApiAdmin]
    pagination_class = CyberComCursorPagination

    @action(detail=True, methods=["post"], url_path="deprecate")
    def deprecate(self, request, pk=None):
        ver = self.get_object()
        sunset_days = request.data.get("sunset_days", 180)
        _ver_svc.deprecate(ver, sunset_days=sunset_days)
        return Response(ApiVersionSerializer(ver).data)

    @action(detail=True, methods=["post"], url_path="set-current")
    def set_current(self, request, pk=None):
        ver = self.get_object()
        _ver_svc.set_current(ver)
        return Response(ApiVersionSerializer(ver).data)


# ---------------------------------------------------------------------------
# ApiCatalogViewSet
# ---------------------------------------------------------------------------


class ApiCatalogViewSet(viewsets.ModelViewSet):
    queryset = ApiCatalog.objects.select_related("current_version").all()
    serializer_class = ApiCatalogSerializer
    permission_classes = [ReadOnlyOrApiAdmin]
    pagination_class = CyberComCursorPagination

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        cat = self.get_object()
        _catalog_svc.publish(cat)
        return Response(ApiCatalogSerializer(cat).data)

    @action(detail=True, methods=["post"], url_path="deprecate")
    def deprecate(self, request, pk=None):
        cat = self.get_object()
        _catalog_svc.deprecate(cat)
        return Response(ApiCatalogSerializer(cat).data)

    @action(detail=True, methods=["get"], url_path="openapi")
    def openapi_spec(self, request, pk=None):
        cat = self.get_object()
        spec = _sdk_svc.get_openapi_spec(cat)
        return Response(spec)

    @action(detail=True, methods=["get"], url_path="endpoints")
    def endpoints(self, request, pk=None):
        cat = self.get_object()
        eps = cat.endpoints.all()
        return Response(ApiEndpointSerializer(eps, many=True).data)

    @action(detail=True, methods=["get", "post"], url_path="scopes")
    def scopes(self, request, pk=None):
        cat = self.get_object()
        if request.method == "GET":
            return Response(ApiScopeSerializer(cat.scopes.all(), many=True).data)
        ser = ApiScopeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        scope = _catalog_svc.add_scope(
            cat,
            ser.validated_data["name"],
            ser.validated_data["description"],
            ser.validated_data.get("is_sensitive", False),
        )
        return Response(ApiScopeSerializer(scope).data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# ApiApplicationViewSet
# ---------------------------------------------------------------------------


class ApiApplicationViewSet(viewsets.ModelViewSet):
    queryset = ApiApplication.objects.all()
    serializer_class = ApiApplicationSerializer
    permission_classes = [IsApiOwner]
    pagination_class = CyberComCursorPagination

    @action(detail=True, methods=["post"], url_path="suspend")
    def suspend(self, request, pk=None):
        app = self.get_object()
        _app_svc.suspend(app)
        return Response(ApiApplicationSerializer(app).data)

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        app = self.get_object()
        _app_svc.activate(app)
        return Response(ApiApplicationSerializer(app).data)

    @action(detail=True, methods=["get"], url_path="keys")
    def list_keys(self, request, pk=None):
        app = self.get_object()
        keys = app.api_keys.all()
        return Response(ApiKeySerializer(keys, many=True).data)


# ---------------------------------------------------------------------------
# ApiKeyViewSet
# ---------------------------------------------------------------------------


class ApiKeyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ApiKey.objects.all()
    serializer_class = ApiKeySerializer
    permission_classes = [IsApiAdmin]
    pagination_class = CyberComCursorPagination

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        ser = ApiKeyCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            app = ApiApplication.objects.get(pk=ser.validated_data["application_id"])
        except ApiApplication.DoesNotExist:
            return Response(
                {
                    "type": "https://cybercom.io/errors/not_found",
                    "title": "Not Found",
                    "status": 404,
                    "detail": "Application not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        key_obj, raw = _key_svc.generate(
            application=app,
            name=ser.validated_data["name"],
            scopes=ser.validated_data.get("scopes", []),
            expires_in_days=ser.validated_data.get("expires_in_days"),
        )
        data = ApiKeySerializer(key_obj).data
        data["raw_key"] = raw
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="revoke")
    def revoke(self, request, pk=None):
        key = self.get_object()
        ser = ApiKeyRevokeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        _key_svc.revoke(key, revoked_by=ser.validated_data.get("revoked_by", ""))
        return Response(ApiKeySerializer(key).data)

    @action(detail=True, methods=["post"], url_path="rotate")
    def rotate(self, request, pk=None):
        old_key = self.get_object()
        new_key, raw = _key_svc.rotate(old_key, created_by=str(request.user))
        data = ApiKeySerializer(new_key).data
        data["raw_key"] = raw
        return Response(data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# ApiSubscriptionViewSet
# ---------------------------------------------------------------------------


class ApiSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = ApiSubscription.objects.select_related("application", "catalog").all()
    serializer_class = ApiSubscriptionSerializer
    permission_classes = [IsApiOwner]
    pagination_class = CyberComCursorPagination

    @action(detail=False, methods=["post"], url_path="subscribe")
    def subscribe(self, request):
        app_id = request.data.get("application_id")
        cat_id = request.data.get("catalog_id")
        scopes = request.data.get("approved_scopes", [])
        try:
            app = ApiApplication.objects.get(pk=app_id)
            cat = ApiCatalog.objects.get(pk=cat_id)
        except (ApiApplication.DoesNotExist, ApiCatalog.DoesNotExist) as e:
            return Response(
                {
                    "type": "https://cybercom.io/errors/not_found",
                    "title": "Not Found",
                    "status": 404,
                    "detail": str(e),
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        sub = _sub_svc.subscribe(app, cat, approved_scopes=scopes, approved_by=str(request.user))
        return Response(ApiSubscriptionSerializer(sub).data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# ApiRateLimitViewSet
# ---------------------------------------------------------------------------


class ApiRateLimitViewSet(viewsets.ModelViewSet):
    queryset = ApiRateLimit.objects.all()
    serializer_class = ApiRateLimitSerializer
    permission_classes = [IsApiAdmin]
    pagination_class = CyberComCursorPagination


# ---------------------------------------------------------------------------
# ApiPolicyViewSet
# ---------------------------------------------------------------------------


class ApiPolicyViewSet(viewsets.ModelViewSet):
    queryset = ApiPolicy.objects.all()
    serializer_class = ApiPolicySerializer
    permission_classes = [IsApiAdmin]
    pagination_class = CyberComCursorPagination


# ---------------------------------------------------------------------------
# ApiContractViewSet
# ---------------------------------------------------------------------------


class ApiContractViewSet(viewsets.ModelViewSet):
    queryset = ApiContract.objects.all()
    serializer_class = ApiContractSerializer
    permission_classes = [IsApiAdmin]
    pagination_class = CyberComCursorPagination

    @action(detail=True, methods=["post"], url_path="validate")
    def validate(self, request, pk=None):
        contract = self.get_object()
        ser = ApiContractValidateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        is_valid = _contract_svc.validate(contract, ser.validated_data["current_schema"])
        return Response(
            {
                "contract_id": str(contract.id),
                "consumer": contract.consumer_name,
                "is_valid": is_valid,
                "validation_errors": contract.validation_errors,
            }
        )

    @action(detail=False, methods=["post"], url_path="validate-all")
    def validate_all(self, request):
        cat_id = request.data.get("catalog_id")
        try:
            cat = ApiCatalog.objects.get(pk=cat_id)
        except ApiCatalog.DoesNotExist:
            return Response({"detail": "Catalog not found."}, status=status.HTTP_404_NOT_FOUND)
        results = _contract_svc.validate_all(cat)
        return Response({"catalog": cat.slug, "results": results})


# ---------------------------------------------------------------------------
# ApiUsageViewSet
# ---------------------------------------------------------------------------


class ApiUsageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ApiUsage.objects.all()
    serializer_class = ApiUsageSerializer
    permission_classes = [IsApiAdmin]
    pagination_class = ApiUsageCursorPagination

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        from django.db.models import Avg, Count

        qs = self.get_queryset()
        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        agg = qs.aggregate(
            total=Count("id"),
            avg_latency=Avg("latency_ms"),
            errors=Count(
                "id", filter=__import__("django.db.models", fromlist=["Q"]).Q(is_error=True)
            ),
        )
        return Response(agg)


# ---------------------------------------------------------------------------
# ApiWebhookViewSet
# ---------------------------------------------------------------------------


class ApiWebhookViewSet(viewsets.ModelViewSet):
    queryset = ApiWebhook.objects.all()
    serializer_class = ApiWebhookSerializer
    permission_classes = [CanManageWebhooks]
    pagination_class = CyberComCursorPagination

    @action(detail=True, methods=["post"], url_path="pause")
    def pause(self, request, pk=None):
        wh = self.get_object()
        _webhook_svc.pause(wh)
        return Response(ApiWebhookSerializer(wh).data)

    @action(detail=True, methods=["post"], url_path="disable")
    def disable(self, request, pk=None):
        wh = self.get_object()
        _webhook_svc.disable(wh)
        return Response(ApiWebhookSerializer(wh).data)

    @action(detail=False, methods=["post"], url_path="dispatch")
    def dispatch(self, request):
        ser = WebhookDispatchSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        deliveries = _webhook_svc.dispatch(
            event_type=ser.validated_data["event_type"],
            payload=ser.validated_data["payload"],
            tenant_id=ser.validated_data.get("tenant_id"),
        )
        return Response(
            {
                "dispatched": len(deliveries),
                "delivery_ids": [str(d.id) for d in deliveries],
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["get"], url_path="deliveries")
    def deliveries(self, request, pk=None):
        wh = self.get_object()
        qs = wh.deliveries.all().order_by("-created_at")[:50]
        return Response(ApiWebhookDeliverySerializer(qs, many=True).data)


# ---------------------------------------------------------------------------
# IdempotencyKeyViewSet
# ---------------------------------------------------------------------------


class IdempotencyKeyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IdempotencyKey.objects.all()
    serializer_class = IdempotencyKeySerializer
    permission_classes = [IsApiAdmin]
    pagination_class = CyberComCursorPagination

    @action(detail=False, methods=["post"], url_path="purge-expired")
    def purge_expired(self, request):
        count = _idempotency_svc.purge_expired()
        return Response({"purged": count})


# ---------------------------------------------------------------------------
# FHIR Views
# ---------------------------------------------------------------------------


class FHIRResourceView(APIView):
    """
    FHIR R4 / R5 resource endpoint.
    GET  /fhir/{version}/{resource}/        -> Bundle (searchset)
    GET  /fhir/{version}/{resource}/{id}/   -> single resource
    POST /fhir/{version}/{resource}/        -> create
    """

    permission_classes = [IsAuthenticated]
    pagination_class = FHIRBundlePagination

    def get(self, request, fhir_version="R4", resource_type=None, resource_id=None):
        if fhir_version not in _fhir_svc.SUPPORTED_VERSIONS:
            return Response(
                _fhir_svc.build_operation_outcome(
                    "error", "not-supported", f"FHIR version {fhir_version} not supported"
                ),
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/fhir+json",
            )
        if not _fhir_svc.is_supported(resource_type or ""):
            return Response(
                _fhir_svc.build_operation_outcome(
                    "error", "not-supported", f"Resource type {resource_type} not supported"
                ),
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/fhir+json",
            )

        if resource_id:
            resource = self._build_single(resource_type, resource_id)
            return Response(resource, content_type="application/fhir+json")

        resources = self._search(resource_type, request)
        bundle = _fhir_svc.build_bundle(resource_type, resources)
        return Response(bundle, content_type="application/fhir+json")

    def post(self, request, fhir_version="R4", resource_type=None, resource_id=None):
        import uuid as _uuid

        if not _fhir_svc.is_supported(resource_type or ""):
            return Response(
                _fhir_svc.build_operation_outcome(
                    "error", "not-supported", f"Resource type {resource_type} not supported"
                ),
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/fhir+json",
            )
        new_id = str(_uuid.uuid4())
        resource = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        resource["id"] = new_id
        resource["resourceType"] = resource_type
        return Response(
            resource, status=status.HTTP_201_CREATED, content_type="application/fhir+json"
        )

    def _build_single(self, resource_type: str, resource_id: str) -> dict:
        builders = {
            "Patient": lambda: _fhir_svc.build_patient(resource_id),
            "Encounter": lambda: _fhir_svc.build_encounter(resource_id, "unknown"),
            "Observation": lambda: _fhir_svc.build_observation(
                resource_id, "unknown", "55284-4", "N/A"
            ),
        }
        builder = builders.get(resource_type)
        if builder:
            return builder()
        return {"resourceType": resource_type, "id": resource_id}

    def _search(self, resource_type: str, request) -> list:
        patient_id = request.query_params.get("patient") or "demo-patient"
        if resource_type == "Patient":
            return [_fhir_svc.build_patient(patient_id)]
        if resource_type == "Encounter":
            return [_fhir_svc.build_encounter("enc-1", patient_id)]
        if resource_type == "Observation":
            return [_fhir_svc.build_observation("obs-1", patient_id, "55284-4", "Normal")]
        return []


# ---------------------------------------------------------------------------
# SDK Generation
# ---------------------------------------------------------------------------


class SDKGenerateView(APIView):
    permission_classes = [IsApiAdmin]

    def post(self, request):
        ser = SDKGenerateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            cat = ApiCatalog.objects.get(slug=ser.validated_data["catalog_slug"])
        except ApiCatalog.DoesNotExist:
            return Response({"detail": "Catalog not found."}, status=status.HTTP_404_NOT_FOUND)

        lang = ser.validated_data["language"]
        if lang == "typescript":
            code = _sdk_svc.generate_typescript_stub(cat)
        else:
            code = _sdk_svc.generate_python_stub(cat)

        return Response(
            {
                "catalog": cat.slug,
                "language": lang,
                "sdk_stub": code,
            }
        )


# ---------------------------------------------------------------------------
# API Metrics (Prometheus)
# ---------------------------------------------------------------------------


class ApiMetricsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from .services import ApiMetrics

        metrics = ApiMetrics().render_prometheus()
        return HttpResponse(metrics, content_type="text/plain; version=0.0.4")


# ---------------------------------------------------------------------------
# OpenAPI Spec View
# ---------------------------------------------------------------------------


class OpenAPISpecView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, catalog_slug=None):
        if catalog_slug:
            try:
                cat = ApiCatalog.objects.get(slug=catalog_slug)
                spec = _sdk_svc.get_openapi_spec(cat)
                return Response(spec)
            except ApiCatalog.DoesNotExist:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "openapi": "3.1.0",
                "info": {"title": "CyberCom Platform API", "version": "1.0.0"},
                "paths": {},
            }
        )
