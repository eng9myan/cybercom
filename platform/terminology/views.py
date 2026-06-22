from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from platform.terminology.models import TerminologyAuditLog
from platform.terminology.serializers import (
    TerminologyAuditLogSerializer, TerminologySearchSerializer,
    TerminologyLookupSerializer, TerminologyValidateSerializer,
    TerminologyTranslateSerializer, TerminologyExpandSerializer,
    TerminologySubsumesSerializer
)
from platform.terminology.services import TerminologyService

class TerminologyViewSet(viewsets.ViewSet):
    """
    ViewSet exposing clinical terminology operations (search, lookup, validate, translate, expand).
    Delegates commands to the terminology adapter service layer.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def search(self, request):
        ser = TerminologySearchSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        res = TerminologyService.search(
            provider=ser.validated_data["provider"],
            query=ser.validated_data["query"],
            tenant_id=str(ser.validated_data["tenant_id"]),
            requested_by=str(request.user),
            limit=ser.validated_data.get("limit", 10)
        )
        return Response(res, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def lookup(self, request):
        ser = TerminologyLookupSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        res = TerminologyService.lookup(
            provider=ser.validated_data["provider"],
            code=ser.validated_data["code"],
            tenant_id=str(ser.validated_data["tenant_id"]),
            requested_by=str(request.user),
            system=ser.validated_data.get("system")
        )
        if res is None:
            return Response({"detail": "Concept not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(res, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def validate(self, request):
        ser = TerminologyValidateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        is_valid = TerminologyService.validate(
            provider=ser.validated_data["provider"],
            code=ser.validated_data["code"],
            tenant_id=str(ser.validated_data["tenant_id"]),
            requested_by=str(request.user),
            system=ser.validated_data.get("system"),
            value_set=ser.validated_data.get("value_set")
        )
        return Response({"valid": is_valid}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def translate(self, request):
        ser = TerminologyTranslateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        res = TerminologyService.translate(
            provider=ser.validated_data["provider"],
            code=ser.validated_data["code"],
            target_system=ser.validated_data["target_system"],
            tenant_id=str(ser.validated_data["tenant_id"]),
            requested_by=str(request.user),
            concept_map=ser.validated_data.get("concept_map")
        )
        if res is None:
            return Response({"detail": "Translation mapping not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(res, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def expand(self, request):
        ser = TerminologyExpandSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        res = TerminologyService.expand(
            provider=ser.validated_data["provider"],
            value_set=ser.validated_data["value_set"],
            tenant_id=str(ser.validated_data["tenant_id"]),
            requested_by=str(request.user),
            filter_str=ser.validated_data.get("filter_str")
        )
        return Response(res, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def subsumes(self, request):
        ser = TerminologySubsumesSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        outcome = TerminologyService.subsumes(
            provider=ser.validated_data["provider"],
            code_a=ser.validated_data["code_a"],
            code_b=ser.validated_data["code_b"],
            tenant_id=str(ser.validated_data["tenant_id"]),
            requested_by=str(request.user),
            system=ser.validated_data.get("system")
        )
        return Response({"outcome": outcome}, status=status.HTTP_200_OK)


class TerminologyAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset to monitor clinical terminology access audit logs.
    """
    queryset = TerminologyAuditLog.objects.all().order_by("-timestamp")
    serializer_class = TerminologyAuditLogSerializer
    permission_classes = [IsAuthenticated]
