from .models import LabOperationsDashboard, LabTurnaroundMetric, LabProductivityReport, LabQualityDashboard, LabMicrobiologyDashboard
from .serializers import LabOperationsDashboardSerializer, LabTurnaroundMetricSerializer, LabProductivityReportSerializer, LabQualityDashboardSerializer, LabMicrobiologyDashboardSerializer
from ..views import LaboratoryModelViewSet

class LabOperationsDashboardViewSet(LaboratoryModelViewSet):
    queryset = LabOperationsDashboard.objects.all()
    serializer_class = LabOperationsDashboardSerializer
    required_feature = "lab.analytics"
    filterset_fields = ["snapshot_date", "department"]

class LabTurnaroundMetricViewSet(LaboratoryModelViewSet):
    queryset = LabTurnaroundMetric.objects.all()
    serializer_class = LabTurnaroundMetricSerializer
    required_feature = "lab.analytics"
    filterset_fields = ["department", "period_type", "period_start"]

class LabProductivityReportViewSet(LaboratoryModelViewSet):
    queryset = LabProductivityReport.objects.all()
    serializer_class = LabProductivityReportSerializer
    required_feature = "lab.analytics"
    filterset_fields = ["technologist_id", "period_type", "period_start"]

class LabQualityDashboardViewSet(LaboratoryModelViewSet):
    queryset = LabQualityDashboard.objects.all()
    serializer_class = LabQualityDashboardSerializer
    required_feature = "lab.analytics"
    filterset_fields = ["department", "period_year", "period_month"]

class LabMicrobiologyDashboardViewSet(LaboratoryModelViewSet):
    queryset = LabMicrobiologyDashboard.objects.all()
    serializer_class = LabMicrobiologyDashboardSerializer
    required_feature = "lab.analytics"
    filterset_fields = ["period_year", "period_month"]
