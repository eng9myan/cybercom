from products.cymed.hospital.views import HospitalModelViewSet
from products.cymed.hospital.capacity_management.models import CapacityRule, CapacityThreshold, SurgePlan, OverflowUnit
from products.cymed.hospital.capacity_management.serializers import (
    CapacityRuleSerializer, CapacityThresholdSerializer, SurgePlanSerializer,
    OverflowUnitSerializer
)

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
