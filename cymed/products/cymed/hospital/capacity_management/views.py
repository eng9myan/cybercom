from products.cymed.hospital.capacity_management.models import (
    CapacityRule,
    CapacityThreshold,
    OverflowUnit,
    SurgePlan,
)
from products.cymed.hospital.capacity_management.serializers import (
    CapacityRuleSerializer,
    CapacityThresholdSerializer,
    OverflowUnitSerializer,
    SurgePlanSerializer,
)
from products.cymed.hospital.views import HospitalModelViewSet


class CapacityRuleViewSet(HospitalModelViewSet):
    queryset = CapacityRule.objects.all()
    serializer_class = CapacityRuleSerializer


class CapacityThresholdViewSet(HospitalModelViewSet):
    queryset = CapacityThreshold.objects.all()
    serializer_class = CapacityThresholdSerializer


class SurgePlanViewSet(HospitalModelViewSet):
    queryset = SurgePlan.objects.all()
    serializer_class = SurgePlanSerializer


class OverflowUnitViewSet(HospitalModelViewSet):
    queryset = OverflowUnit.objects.all()
    serializer_class = OverflowUnitSerializer
