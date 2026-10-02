from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from platform.api.permissions import actor
from products.cymed.hospital.nursing import mar
from products.cymed.hospital.nursing.models import (
    MedicationAdministration,
    NursingAssessment,
    NursingAssignment,
    NursingCarePlan,
    NursingHandover,
    NursingShift,
    NursingTask,
)
from products.cymed.hospital.nursing.serializers import (
    AdministerSerializer,
    GenerateScheduleSerializer,
    MedicationAdministrationSerializer,
    NotGivenSerializer,
    PrnSerializer,
    NursingAssessmentSerializer,
    NursingAssignmentSerializer,
    NursingCarePlanSerializer,
    NursingHandoverSerializer,
    NursingShiftSerializer,
    NursingTaskSerializer,
)
from products.cymed.hospital.views import HospitalModelViewSet


class NursingShiftViewSet(HospitalModelViewSet):
    queryset = NursingShift.objects.all()
    serializer_class = NursingShiftSerializer


class NursingAssignmentViewSet(HospitalModelViewSet):
    queryset = NursingAssignment.objects.all()
    serializer_class = NursingAssignmentSerializer


class NursingAssessmentViewSet(HospitalModelViewSet):
    queryset = NursingAssessment.objects.all()
    serializer_class = NursingAssessmentSerializer


class NursingCarePlanViewSet(HospitalModelViewSet):
    queryset = NursingCarePlan.objects.all()
    serializer_class = NursingCarePlanSerializer


class NursingTaskViewSet(HospitalModelViewSet):
    queryset = NursingTask.objects.all()
    serializer_class = NursingTaskSerializer


class NursingHandoverViewSet(HospitalModelViewSet):
    queryset = NursingHandover.objects.all()
    serializer_class = NursingHandoverSerializer


def _nurse(request) -> str:
    return actor(request)


def _mar_error(exc):
    return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class MedicationAdministrationViewSet(HospitalModelViewSet):
    """Electronic Medication Administration Record.

    GET  /mar/?admission_id=&patient_id=&status=&due_before=   the worklist
    POST /mar/generate/        schedule doses for a verified order
    POST /mar/{id}/administer/ give a scheduled dose (five-rights checked)
    POST /mar/{id}/not-given/  held / refused / missed, with reason
    POST /mar/prn/             an as-needed dose with its indication
    """

    queryset = MedicationAdministration.objects.select_related("medication_order")
    serializer_class = MedicationAdministrationSerializer
    http_method_names = ["get", "post", "head", "options"]
    filterset_fields = ["admission_id", "patient_id", "status"]

    def create(self, request, *args, **kwargs):
        return Response({"detail": "Use generate, administer, prn or not-given."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get_queryset(self):
        qs = super().get_queryset()
        due_before = self.request.query_params.get("due_before")
        if due_before:
            qs = qs.filter(scheduled_at__lte=due_before)
        return qs

    def _order(self, request, order_id):
        from products.cymed.pharmacy.prescriptions.models import MedicationOrder

        return MedicationOrder.objects.filter(id=order_id, tenant_id=request.tenant_id).first()

    @action(detail=False, methods=["post"])
    def generate(self, request):
        ser = GenerateScheduleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        order = self._order(request, ser.validated_data["medication_order"])
        if order is None:
            return Response({"detail": "Medication order not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            rows = mar.generate_schedule(order, hours=ser.validated_data["hours"])
        except mar.MarError as exc:
            return _mar_error(exc)
        return Response(self.get_serializer(rows, many=True).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def administer(self, request, pk=None):
        ser = AdministerSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            row = mar.administer(self.get_object(), nurse=_nurse(request), **ser.validated_data)
        except mar.MarError as exc:
            return _mar_error(exc)
        return Response(self.get_serializer(row).data)

    @action(detail=True, methods=["post"], url_path="not-given")
    def not_given(self, request, pk=None):
        ser = NotGivenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            row = mar.mark_not_given(self.get_object(), nurse=_nurse(request), **ser.validated_data)
        except mar.MarError as exc:
            return _mar_error(exc)
        return Response(self.get_serializer(row).data)

    @action(detail=False, methods=["post"])
    def prn(self, request):
        ser = PrnSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = dict(ser.validated_data)
        order = self._order(request, data.pop("medication_order"))
        if order is None:
            return Response({"detail": "Medication order not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            row = mar.administer_prn(order, nurse=_nurse(request), **data)
        except mar.MarError as exc:
            return _mar_error(exc)
        return Response(self.get_serializer(row).data, status=status.HTTP_201_CREATED)
