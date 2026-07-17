from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DrfValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from platform.tenant.permissions import IsPlatformAdmin
from products.cycom.cyai_moduledev import services
from products.cycom.cyai_moduledev.discovery import discover_apps
from products.cycom.cyai_moduledev.models import ModuleDevRequest
from products.cycom.cyai_moduledev.serializers import (
    ApproveProductionSerializer,
    DeployProductionSerializer,
    GenerateCodeSerializer,
    ModuleDevRequestSerializer,
    SendMessageSerializer,
    StartRequestSerializer,
)


def _as_drf_error(exc):
    return DrfValidationError(str(exc))


class ModuleDevRequestViewSet(TenantScopedModelViewSet):
    queryset = ModuleDevRequest.objects.all()
    serializer_class = ModuleDevRequestSerializer
    http_method_names = ["get", "post", "head", "options"]  # every mutation goes through an action

    @action(detail=False, methods=["get"], url_path="catalog")
    def catalog(self, request):
        """Discovery Engine's public read: what already exists in Cycom."""
        return Response(discover_apps())

    def create(self, request, *args, **kwargs):
        ser = StartRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        claims = getattr(request, "auth_claims", {}) or {}
        req = services.start_request(
            tenant_id=request.tenant_id,
            product_description=ser.validated_data["product_description"],
            requested_by=claims.get("email", ""),
        )
        return Response(ModuleDevRequestSerializer(req).data, status=201)

    @action(detail=True, methods=["post"], url_path="message")
    def message(self, request, pk=None):
        req = self.get_object()
        ser = SendMessageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            result = services.send_requirements_message(req, ser.validated_data["content"])
        except Exception as exc:  # noqa: BLE001
            raise _as_drf_error(exc)
        return Response(result)

    @action(detail=True, methods=["post"], url_path="confirm-requirements")
    def confirm_requirements(self, request, pk=None):
        req = self.get_object()
        claims = getattr(request, "auth_claims", {}) or {}
        try:
            services.confirm_requirements(req, claims.get("email", ""))
        except Exception as exc:  # noqa: BLE001
            raise _as_drf_error(exc)
        return Response(ModuleDevRequestSerializer(req).data)

    @action(detail=True, methods=["post"], url_path="generate-design")
    def generate_design(self, request, pk=None):
        req = self.get_object()
        try:
            services.generate_technical_design(req)
        except Exception as exc:  # noqa: BLE001
            raise _as_drf_error(exc)
        return Response(ModuleDevRequestSerializer(req).data)

    @action(
        detail=True, methods=["post"], url_path="approve-design", permission_classes=[IsPlatformAdmin]
    )
    def approve_design(self, request, pk=None):
        req = self.get_object()
        claims = getattr(request, "auth_claims", {}) or {}
        try:
            services.approve_technical_design(req, claims.get("email", ""))
        except Exception as exc:  # noqa: BLE001
            raise _as_drf_error(exc)
        return Response(ModuleDevRequestSerializer(req).data)

    @action(detail=True, methods=["post"], url_path="generate-code")
    def generate_code(self, request, pk=None):
        req = self.get_object()
        ser = GenerateCodeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            services.generate_code(req, ser.validated_data["module_name"])
        except Exception as exc:  # noqa: BLE001
            raise _as_drf_error(exc)
        return Response(ModuleDevRequestSerializer(req).data)

    @action(detail=True, methods=["post"], url_path="run-checks")
    def run_checks(self, request, pk=None):
        req = self.get_object()
        try:
            services.run_checks(req)
        except Exception as exc:  # noqa: BLE001
            raise _as_drf_error(exc)
        return Response(ModuleDevRequestSerializer(req).data)

    @action(
        detail=True, methods=["post"], url_path="deploy-staging", permission_classes=[IsPlatformAdmin]
    )
    def deploy_staging(self, request, pk=None):
        req = self.get_object()
        try:
            services.deploy_to_staging(req)
        except Exception as exc:  # noqa: BLE001
            raise _as_drf_error(exc)
        return Response(ModuleDevRequestSerializer(req).data)

    @action(detail=True, methods=["post"], url_path="mark-uat")
    def mark_uat(self, request, pk=None):
        req = self.get_object()
        try:
            services.mark_uat(req)
        except Exception as exc:  # noqa: BLE001
            raise _as_drf_error(exc)
        return Response(ModuleDevRequestSerializer(req).data)

    @action(
        detail=True, methods=["post"], url_path="approve-production", permission_classes=[IsPlatformAdmin]
    )
    def approve_production(self, request, pk=None):
        req = self.get_object()
        ser = ApproveProductionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        claims = getattr(request, "auth_claims", {}) or {}
        try:
            services.approve_production(
                req, claims.get("email", ""), ser.validated_data["confirm_production"]
            )
        except Exception as exc:  # noqa: BLE001
            raise _as_drf_error(exc)
        return Response(ModuleDevRequestSerializer(req).data)

    @action(
        detail=True, methods=["post"], url_path="deploy-production", permission_classes=[IsPlatformAdmin]
    )
    def deploy_production(self, request, pk=None):
        req = self.get_object()
        ser = DeployProductionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            services.deploy_to_production(req, ser.validated_data["confirm_push"])
        except Exception as exc:  # noqa: BLE001
            raise _as_drf_error(exc)
        return Response(ModuleDevRequestSerializer(req).data)

    @action(
        detail=True, methods=["post"], url_path="rollback", permission_classes=[IsPlatformAdmin]
    )
    def rollback(self, request, pk=None):
        req = self.get_object()
        try:
            services.rollback(req)
        except Exception as exc:  # noqa: BLE001
            raise _as_drf_error(exc)
        return Response(ModuleDevRequestSerializer(req).data)
