from products.cymed.hospital.adt.models import (
    Admission,
    AdmissionReason,
    AdmissionType,
    DischargeDisposition,
    DischargeReason,
    DischargeSummary,
    TransferApproval,
    TransferRequest,
)
from products.cymed.hospital.adt.serializers import (
    AdmissionReasonSerializer,
    AdmissionSerializer,
    AdmissionTypeSerializer,
    DischargeDispositionSerializer,
    DischargeReasonSerializer,
    DischargeSummarySerializer,
    TransferApprovalSerializer,
    TransferRequestSerializer,
)
from products.cymed.hospital.views import HospitalModelViewSet


class AdmissionReasonViewSet(HospitalModelViewSet):
    queryset = AdmissionReason.objects.all()
    serializer_class = AdmissionReasonSerializer


class AdmissionTypeViewSet(HospitalModelViewSet):
    queryset = AdmissionType.objects.all()
    serializer_class = AdmissionTypeSerializer


class DischargeReasonViewSet(HospitalModelViewSet):
    queryset = DischargeReason.objects.all()
    serializer_class = DischargeReasonSerializer


class DischargeDispositionViewSet(HospitalModelViewSet):
    queryset = DischargeDisposition.objects.all()
    serializer_class = DischargeDispositionSerializer


class AdmissionViewSet(HospitalModelViewSet):
    queryset = Admission.objects.all()
    serializer_class = AdmissionSerializer


class TransferRequestViewSet(HospitalModelViewSet):
    queryset = TransferRequest.objects.all()
    serializer_class = TransferRequestSerializer


class TransferApprovalViewSet(HospitalModelViewSet):
    queryset = TransferApproval.objects.all()
    serializer_class = TransferApprovalSerializer


class DischargeSummaryViewSet(HospitalModelViewSet):
    queryset = DischargeSummary.objects.all()
    serializer_class = DischargeSummarySerializer
