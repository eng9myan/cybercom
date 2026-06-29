from products.cymed.hospital.transfer_center.models import (
    AcceptanceReview,
    ExternalReferral,
    ReceivingFacility,
    TransferCase,
)
from products.cymed.hospital.transfer_center.serializers import (
    AcceptanceReviewSerializer,
    ExternalReferralSerializer,
    ReceivingFacilitySerializer,
    TransferCaseSerializer,
)
from products.cymed.hospital.views import HospitalModelViewSet


class ReceivingFacilityViewSet(HospitalModelViewSet):
    queryset = ReceivingFacility.objects.all()
    serializer_class = ReceivingFacilitySerializer


class TransferCaseViewSet(HospitalModelViewSet):
    queryset = TransferCase.objects.all()
    serializer_class = TransferCaseSerializer


class ExternalReferralViewSet(HospitalModelViewSet):
    queryset = ExternalReferral.objects.all()
    serializer_class = ExternalReferralSerializer


class AcceptanceReviewViewSet(HospitalModelViewSet):
    queryset = AcceptanceReview.objects.all()
    serializer_class = AcceptanceReviewSerializer
