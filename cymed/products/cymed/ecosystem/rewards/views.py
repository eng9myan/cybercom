"""ViewSets for CyMed ecosystem-wide loyalty API."""
from __future__ import annotations

from decimal import Decimal

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import (
    EcosystemAccount,
    EcosystemPointsEvent,
    EcosystemProgram,
    EcosystemRedemption,
    EcosystemReward,
    EcosystemTier,
)
from .serializers import (
    EcosystemAccountSerializer,
    EcosystemPointsEventSerializer,
    EcosystemProgramSerializer,
    EcosystemRedemptionSerializer,
    EcosystemRewardSerializer,
    EcosystemTierSerializer,
)


class EcosystemProgramViewSet(viewsets.ModelViewSet):
    queryset = EcosystemProgram.objects.all()
    serializer_class = EcosystemProgramSerializer

    @action(detail=False, methods=["post"], url_path="enroll")
    def enroll(self, request):
        account = services.enroll(
            program_id=request.data.get("program_id"),
            patient_profile_id=request.data.get("patient_profile_id"),
            primary_country=request.data.get("primary_country", ""),
        )
        return Response(EcosystemAccountSerializer(account).data)


class EcosystemAccountViewSet(viewsets.ModelViewSet):
    queryset = EcosystemAccount.objects.all()
    serializer_class = EcosystemAccountSerializer

    @action(detail=True, methods=["post"], url_path="earn")
    def earn(self, request, pk=None):
        event = services.earn(
            account_id=pk,
            source_tenant_id=request.data.get("source_tenant_id"),
            currency_amount=Decimal(str(request.data.get("currency_amount", "0"))),
            reference_kind=request.data.get("reference_kind", ""),
            reference_id=request.data.get("reference_id"),
            reason=request.data.get("reason", ""),
        )
        return Response(EcosystemPointsEventSerializer(event).data)

    @action(detail=True, methods=["post"], url_path="redeem")
    def redeem(self, request, pk=None):
        redemption = services.redeem(
            account_id=pk,
            reward_id=request.data.get("reward_id"),
            redeemed_at_tenant_id=request.data.get("redeemed_at_tenant_id"),
        )
        return Response(EcosystemRedemptionSerializer(redemption).data)

    @action(detail=True, methods=["post"], url_path="transfer-out")
    def transfer_out(self, request, pk=None):
        event = services.transfer_out(
            account_id=pk,
            other_account_id=request.data.get("other_account_id"),
            points=int(request.data.get("points", 0)),
            reason=request.data.get("reason", ""),
        )
        return Response(EcosystemPointsEventSerializer(event).data)

    @action(detail=True, methods=["post"], url_path="expire")
    def expire(self, request, pk=None):
        event = services.expire(
            account_id=pk,
            points=int(request.data.get("points", 0)),
            reason=request.data.get("reason", "scheduled"),
        )
        return Response(EcosystemPointsEventSerializer(event).data)

    @action(detail=True, methods=["post"], url_path="manual-adjust")
    def manual_adjust(self, request, pk=None):
        event = services.manual_adjust(
            account_id=pk,
            points=int(request.data.get("points", 0)),
            reason=request.data.get("reason", ""),
        )
        return Response(EcosystemPointsEventSerializer(event).data)


class EcosystemTierViewSet(viewsets.ModelViewSet):
    queryset = EcosystemTier.objects.all()
    serializer_class = EcosystemTierSerializer


class EcosystemPointsEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EcosystemPointsEvent.objects.all()
    serializer_class = EcosystemPointsEventSerializer


class EcosystemRewardViewSet(viewsets.ModelViewSet):
    queryset = EcosystemReward.objects.all()
    serializer_class = EcosystemRewardSerializer


class EcosystemRedemptionViewSet(viewsets.ModelViewSet):
    queryset = EcosystemRedemption.objects.all()
    serializer_class = EcosystemRedemptionSerializer
