from products.cymed.imaging.views import ImagingModelViewSet

from .models import DICOMInstance, DICOMSeries, DICOMStudy, StudyArchive
from .serializers import (
    DICOMInstanceSerializer,
    DICOMSeriesSerializer,
    DICOMStudySerializer,
    StudyArchiveSerializer,
)


class DICOMStudyViewSet(ImagingModelViewSet):
    queryset = DICOMStudy.objects.prefetch_related("series")
    serializer_class = DICOMStudySerializer
    required_feature = "imaging.dicom"


class DICOMSeriesViewSet(ImagingModelViewSet):
    queryset = DICOMSeries.objects.select_related("study").prefetch_related("instances")
    serializer_class = DICOMSeriesSerializer
    required_feature = "imaging.dicom"


class DICOMInstanceViewSet(ImagingModelViewSet):
    queryset = DICOMInstance.objects.select_related("series")
    serializer_class = DICOMInstanceSerializer
    required_feature = "imaging.dicom"


class StudyArchiveViewSet(ImagingModelViewSet):
    queryset = StudyArchive.objects.select_related("study")
    serializer_class = StudyArchiveSerializer
    required_feature = "imaging.dicom"
