"""ViewSets exposing the cross-provider referral routing engine."""
from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import NetworkReferral, RoutingLog, RoutingRule
from .serializers import (
    NetworkReferralSerializer,
    RoutingLogSerializer,
    RoutingRuleSerializer,
)


class RoutingRuleViewSet(viewsets.ModelViewSet):
    queryset = RoutingRule.objects.all()
    serializer_class = RoutingRuleSerializer

    @action(detail=False, methods=["post"], url_path="create-rule")
    def create_rule(self, request):
        data = request.data
        rule = services.create_rule(
            tenant_id=data.get("tenant_id"),
            code=data["code"],
            name=data["name"],
            source_kind=data["source_kind"],
            target_kind=data["target_kind"],
            specialty=data.get("specialty", ""),
            urgency=data.get("urgency", "routine"),
            geo_scope=data.get("geo_scope", "same_country"),
            preferred_tenant_ids=data.get("preferred_tenant_ids"),
            fallback_tenant_ids=data.get("fallback_tenant_ids"),
            payer_ids=data.get("payer_ids"),
            priority=data.get("priority", 100),
        )
        return Response(RoutingRuleSerializer(rule).data)


class NetworkReferralViewSet(viewsets.ModelViewSet):
    queryset = NetworkReferral.objects.all()
    serializer_class = NetworkReferralSerializer

    @action(detail=False, methods=["post"], url_path="route")
    def route(self, request):
        data = request.data
        referral = services.route_referral(
            source_tenant_id=data["source_tenant_id"],
            source_provider_id=data.get("source_provider_id"),
            target_kind=data["target_kind"],
            patient_profile_id=data["patient_profile_id"],
            reason=data["reason"],
            clinical_summary=data.get("clinical_summary", ""),
            urgency=data.get("urgency", "routine"),
            specialty=data.get("specialty", ""),
            preferred_locations=data.get("preferred_locations"),
            consent_grant_id=data.get("consent_grant_id"),
        )
        return Response(NetworkReferralSerializer(referral).data)

    @action(detail=True, methods=["post"], url_path="acknowledge")
    def acknowledge(self, request, pk=None):
        referral = services.acknowledge(
            referral_id=pk,
            target_provider_id=request.data.get("target_provider_id"),
        )
        return Response(NetworkReferralSerializer(referral).data)

    @action(detail=True, methods=["post"], url_path="decline")
    def decline(self, request, pk=None):
        referral = services.decline(
            referral_id=pk,
            reason=request.data.get("reason", ""),
        )
        return Response(NetworkReferralSerializer(referral).data)

    @action(detail=True, methods=["post"], url_path="manual-override")
    def manual_override(self, request, pk=None):
        referral = services.manual_override(
            referral_id=pk,
            target_tenant_id=request.data["target_tenant_id"],
            target_provider_id=request.data.get("target_provider_id"),
            reason=request.data.get("reason", ""),
        )
        return Response(NetworkReferralSerializer(referral).data)

    @action(detail=True, methods=["post"], url_path="mark-scheduled")
    def mark_scheduled(self, request, pk=None):
        referral = services.mark_scheduled(
            referral_id=pk,
            scheduled_at=request.data.get("scheduled_at"),
        )
        return Response(NetworkReferralSerializer(referral).data)

    @action(detail=True, methods=["post"], url_path="mark-completed")
    def mark_completed(self, request, pk=None):
        referral = services.mark_completed(referral_id=pk)
        return Response(NetworkReferralSerializer(referral).data)

    @action(detail=True, methods=["post"], url_path="attach-result")
    def attach_result(self, request, pk=None):
        referral = services.attach_result(
            referral_id=pk,
            document_url=request.data["document_url"],
            kind=request.data.get("kind", ""),
        )
        return Response(NetworkReferralSerializer(referral).data)


class RoutingLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RoutingLog.objects.all()
    serializer_class = RoutingLogSerializer
