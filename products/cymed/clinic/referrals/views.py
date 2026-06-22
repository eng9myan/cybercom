from products.cymed.clinic.views import ClinicModelViewSet
from products.cymed.clinic.referrals.models import Referral, ReferralReason, ReferralProvider, ReferralAttachment
from products.cymed.clinic.referrals.serializers import (
    ReferralSerializer, ReferralReasonSerializer, ReferralProviderSerializer, ReferralAttachmentSerializer
)

class ReferralViewSet(ClinicModelViewSet):
    queryset = Referral.objects.all()
    serializer_class = ReferralSerializer

class ReferralReasonViewSet(ClinicModelViewSet):
    queryset = ReferralReason.objects.all()
    serializer_class = ReferralReasonSerializer

class ReferralProviderViewSet(ClinicModelViewSet):
    queryset = ReferralProvider.objects.all()
    serializer_class = ReferralProviderSerializer

class ReferralAttachmentViewSet(ClinicModelViewSet):
    queryset = ReferralAttachment.objects.all()
    serializer_class = ReferralAttachmentSerializer

