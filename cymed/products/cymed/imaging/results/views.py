from products.cymed.imaging.views import ImagingModelViewSet

from .models import ImagingResult, ResultCommunication, StructuredMeasurement
from .serializers import (
    ImagingResultSerializer,
    ResultCommunicationSerializer,
    StructuredMeasurementSerializer,
)


class ImagingResultViewSet(ImagingModelViewSet):
    queryset = ImagingResult.objects.prefetch_related("measurements", "communications")
    serializer_class = ImagingResultSerializer
    required_feature = "imaging.results"


class StructuredMeasurementViewSet(ImagingModelViewSet):
    queryset = StructuredMeasurement.objects.select_related("result")
    serializer_class = StructuredMeasurementSerializer
    required_feature = "imaging.results"


class ResultCommunicationViewSet(ImagingModelViewSet):
    queryset = ResultCommunication.objects.select_related("result")
    serializer_class = ResultCommunicationSerializer
    required_feature = "imaging.results"
