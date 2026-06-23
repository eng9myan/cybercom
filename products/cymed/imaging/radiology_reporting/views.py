from products.cymed.imaging.views import ImagingModelViewSet
from .models import (
    ReportTemplate, RadiologyReport, RadiologyFinding, RadiologyImpression,
    CriticalFinding, StructuredReport, ReportAmendment,
)
from .serializers import (
    ReportTemplateSerializer, RadiologyReportSerializer, RadiologyFindingSerializer,
    RadiologyImpressionSerializer, CriticalFindingSerializer, StructuredReportSerializer,
    ReportAmendmentSerializer,
)


class ReportTemplateViewSet(ImagingModelViewSet):
    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer
    required_feature = "imaging.reporting"


class RadiologyReportViewSet(ImagingModelViewSet):
    queryset = RadiologyReport.objects.select_related("report_template").prefetch_related(
        "structured_findings", "structured_impressions", "critical_findings", "amendments"
    )
    serializer_class = RadiologyReportSerializer
    required_feature = "imaging.reporting"


class RadiologyFindingViewSet(ImagingModelViewSet):
    queryset = RadiologyFinding.objects.select_related("report")
    serializer_class = RadiologyFindingSerializer
    required_feature = "imaging.reporting"


class RadiologyImpressionViewSet(ImagingModelViewSet):
    queryset = RadiologyImpression.objects.select_related("report")
    serializer_class = RadiologyImpressionSerializer
    required_feature = "imaging.reporting"


class CriticalFindingViewSet(ImagingModelViewSet):
    queryset = CriticalFinding.objects.select_related("report")
    serializer_class = CriticalFindingSerializer
    required_feature = "imaging.reporting"


class StructuredReportViewSet(ImagingModelViewSet):
    queryset = StructuredReport.objects.select_related("report")
    serializer_class = StructuredReportSerializer
    required_feature = "imaging.reporting"


class ReportAmendmentViewSet(ImagingModelViewSet):
    queryset = ReportAmendment.objects.select_related("original_report")
    serializer_class = ReportAmendmentSerializer
    required_feature = "imaging.reporting"
    http_method_names = ["get", "post", "head", "options"]
