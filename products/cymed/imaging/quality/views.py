from products.cymed.imaging.views import ImagingModelViewSet
from .models import QualityAudit, ImagingQualityMetric, RadiationDoseRecord, AccreditationRecord
from .serializers import (
    QualityAuditSerializer, ImagingQualityMetricSerializer,
    RadiationDoseRecordSerializer, AccreditationRecordSerializer,
)


class QualityAuditViewSet(ImagingModelViewSet):
    queryset = QualityAudit.objects.select_related("report")
    serializer_class = QualityAuditSerializer
    required_feature = "imaging.quality"


class ImagingQualityMetricViewSet(ImagingModelViewSet):
    queryset = ImagingQualityMetric.objects.select_related("modality")
    serializer_class = ImagingQualityMetricSerializer
    required_feature = "imaging.quality"


class RadiationDoseRecordViewSet(ImagingModelViewSet):
    queryset = RadiationDoseRecord.objects.all()
    serializer_class = RadiationDoseRecordSerializer
    required_feature = "imaging.quality"


class AccreditationRecordViewSet(ImagingModelViewSet):
    queryset = AccreditationRecord.objects.all()
    serializer_class = AccreditationRecordSerializer
    required_feature = "imaging.quality"
