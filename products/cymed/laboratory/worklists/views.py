from ..views import LaboratoryModelViewSet
from .models import (
    Analyzer,
    AnalyzerInterface,
    AnalyzerMessage,
    AnalyzerResult,
    LabWorklist,
    TechnologistAssignment,
    WorklistItem,
)
from .serializers import (
    AnalyzerInterfaceSerializer,
    AnalyzerMessageSerializer,
    AnalyzerResultSerializer,
    AnalyzerSerializer,
    LabWorklistSerializer,
    TechnologistAssignmentSerializer,
    WorklistItemSerializer,
)


class AnalyzerViewSet(LaboratoryModelViewSet):
    queryset = Analyzer.objects.all()
    serializer_class = AnalyzerSerializer
    required_feature = "lab.worklists"
    filterset_fields = ["analyzer_type", "department", "is_active"]
    search_fields = ["code", "name", "serial_number"]


class AnalyzerInterfaceViewSet(LaboratoryModelViewSet):
    queryset = AnalyzerInterface.objects.select_related("analyzer", "test")
    serializer_class = AnalyzerInterfaceSerializer
    required_feature = "lab.worklists"


class AnalyzerMessageViewSet(LaboratoryModelViewSet):
    queryset = AnalyzerMessage.objects.all()
    serializer_class = AnalyzerMessageSerializer
    required_feature = "lab.worklists"
    filterset_fields = ["analyzer", "direction", "status"]


class AnalyzerResultViewSet(LaboratoryModelViewSet):
    queryset = AnalyzerResult.objects.all()
    serializer_class = AnalyzerResultSerializer
    required_feature = "lab.worklists"
    filterset_fields = ["analyzer", "lab_result_linked"]


class LabWorklistViewSet(LaboratoryModelViewSet):
    queryset = LabWorklist.objects.prefetch_related("items")
    serializer_class = LabWorklistSerializer
    required_feature = "lab.worklists"
    filterset_fields = ["department", "status", "worklist_date"]


class WorklistItemViewSet(LaboratoryModelViewSet):
    queryset = WorklistItem.objects.select_related("worklist", "order_item")
    serializer_class = WorklistItemSerializer
    required_feature = "lab.worklists"
    filterset_fields = ["worklist", "status"]


class TechnologistAssignmentViewSet(LaboratoryModelViewSet):
    queryset = TechnologistAssignment.objects.all()
    serializer_class = TechnologistAssignmentSerializer
    required_feature = "lab.worklists"
    filterset_fields = ["worklist", "status"]
