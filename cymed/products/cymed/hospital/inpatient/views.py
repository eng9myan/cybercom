from products.cymed.hospital.inpatient.models import (
    DailyRound,
    DischargePlanning,
    HospitalStay,
    InpatientCarePlan,
    ProgressReview,
)
from products.cymed.hospital.inpatient.serializers import (
    DailyRoundSerializer,
    DischargePlanningSerializer,
    HospitalStaySerializer,
    InpatientCarePlanSerializer,
    ProgressReviewSerializer,
)
from products.cymed.hospital.views import HospitalModelViewSet


class HospitalStayViewSet(HospitalModelViewSet):
    queryset = HospitalStay.objects.all()
    serializer_class = HospitalStaySerializer


class DailyRoundViewSet(HospitalModelViewSet):
    queryset = DailyRound.objects.all()
    serializer_class = DailyRoundSerializer


class ProgressReviewViewSet(HospitalModelViewSet):
    queryset = ProgressReview.objects.all()
    serializer_class = ProgressReviewSerializer


class InpatientCarePlanViewSet(HospitalModelViewSet):
    queryset = InpatientCarePlan.objects.all()
    serializer_class = InpatientCarePlanSerializer


class DischargePlanningViewSet(HospitalModelViewSet):
    queryset = DischargePlanning.objects.all()
    serializer_class = DischargePlanningSerializer
