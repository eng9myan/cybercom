from products.cymed.hospital.views import HospitalModelViewSet
from products.cymed.hospital.transfer_center.models import ReceivingFacility, TransferCase, ExternalReferral, AcceptanceReview
from products.cymed.hospital.transfer_center.serializers import (
    ReceivingFacilitySerializer, TransferCaseSerializer, ExternalReferralSerializer,
    AcceptanceReviewSerializer
)

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
