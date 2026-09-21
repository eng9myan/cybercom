from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.referrals.models import Referral
from products.cycom.referrals.serializers import ReferralSerializer


class ReferralViewSet(TenantScopedModelViewSet):
    queryset = Referral.objects.select_related("referrer", "applicant").all()
    serializer_class = ReferralSerializer
    filterset_fields = ["referrer", "status"]

    @action(detail=True, methods=["post"], url_path="pay-bonus")
    def pay_bonus(self, request, pk=None):
        referral = self.get_object()
        if referral.status != "hired":
            raise ValidationError("Referral bonus can only be paid once the candidate is hired.")
        if referral.bonus_paid:
            raise ValidationError("Bonus already paid.")
        referral.bonus_paid = True
        referral.save(update_fields=["bonus_paid", "updated_at"])
        return Response(self.get_serializer(referral).data)
