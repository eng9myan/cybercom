"""DRF viewsets for CyMed Pharmacy Loyalty & Rewards."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import (
    LoyaltyProgram,
    LoyaltyTier,
    PatientLoyaltyAccount,
    PointsTransaction,
    Redemption,
    Reward,
)
from .serializers import (
    LoyaltyProgramSerializer,
    LoyaltyTierSerializer,
    PatientLoyaltyAccountSerializer,
    PointsTransactionSerializer,
    RedemptionSerializer,
    RewardSerializer,
)


class LoyaltyProgramViewSet(viewsets.ModelViewSet):
    queryset = LoyaltyProgram.objects.all()
    serializer_class = LoyaltyProgramSerializer


class LoyaltyTierViewSet(viewsets.ModelViewSet):
    queryset = LoyaltyTier.objects.all()
    serializer_class = LoyaltyTierSerializer


class PatientLoyaltyAccountViewSet(viewsets.ModelViewSet):
    queryset = PatientLoyaltyAccount.objects.all()
    serializer_class = PatientLoyaltyAccountSerializer

    @action(detail=False, methods=["post"], url_path="enroll")
    def enroll(self, request):
        data = request.data
        account = services.enroll(
            tenant_id=data["tenant_id"],
            program_id=data["program_id"],
            patient_profile_id=data["patient_profile_id"],
        )
        return Response(PatientLoyaltyAccountSerializer(account).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="earn-points")
    def earn_points(self, request, pk=None):
        data = request.data
        txn = services.earn_points(
            account_id=pk,
            points=int(data["points"]),
            reason=data.get("reason", ""),
            reference_order_id=data.get("reference_order_id"),
            expires_at=data.get("expires_at"),
        )
        return Response(PointsTransactionSerializer(txn).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="redeem-reward")
    def redeem_reward(self, request, pk=None):
        data = request.data
        redemption = services.redeem_reward(
            account_id=pk,
            reward_id=data["reward_id"],
            code=data.get("code", ""),
        )
        return Response(RedemptionSerializer(redemption).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="manual-adjust")
    def manual_adjust(self, request, pk=None):
        data = request.data
        txn = services.manual_adjust(
            account_id=pk,
            points=int(data["points"]),
            direction=data.get("direction", "up"),
            reason=data.get("reason", ""),
        )
        return Response(PointsTransactionSerializer(txn).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="expire-points")
    def expire_points(self, request, pk=None):
        data = request.data
        txn = services.expire_points(
            account_id=pk,
            points=int(data["points"]),
            reason=data.get("reason", ""),
        )
        return Response(PointsTransactionSerializer(txn).data, status=status.HTTP_201_CREATED)


class PointsTransactionViewSet(viewsets.ModelViewSet):
    queryset = PointsTransaction.objects.all()
    serializer_class = PointsTransactionSerializer


class RewardViewSet(viewsets.ModelViewSet):
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer


class RedemptionViewSet(viewsets.ModelViewSet):
    queryset = Redemption.objects.all()
    serializer_class = RedemptionSerializer
