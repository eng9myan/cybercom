from products.cymed.hospital.nursing.models import (
    NursingAssessment,
    NursingAssignment,
    NursingCarePlan,
    NursingHandover,
    NursingShift,
    NursingTask,
)
from products.cymed.hospital.nursing.serializers import (
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
