from products.cymed.imaging.views import ImagingModelViewSet

from .models import ReadingAssignment, ReadingQueue, SecondOpinion, TeleradiologyCase
from .serializers import (
    ReadingAssignmentSerializer,
    ReadingQueueSerializer,
    SecondOpinionSerializer,
    TeleradiologyCaseSerializer,
)


class ReadingQueueViewSet(ImagingModelViewSet):
    queryset = ReadingQueue.objects.all()
    serializer_class = ReadingQueueSerializer
    required_feature = "imaging.teleradiology"


class TeleradiologyCaseViewSet(ImagingModelViewSet):
    queryset = TeleradiologyCase.objects.select_related("reading_queue").prefetch_related(
        "assignments"
    )
    serializer_class = TeleradiologyCaseSerializer
    required_feature = "imaging.teleradiology"


class ReadingAssignmentViewSet(ImagingModelViewSet):
    queryset = ReadingAssignment.objects.select_related("teleradiology_case")
    serializer_class = ReadingAssignmentSerializer
    required_feature = "imaging.teleradiology"


class SecondOpinionViewSet(ImagingModelViewSet):
    queryset = SecondOpinion.objects.select_related("original_report")
    serializer_class = SecondOpinionSerializer
    required_feature = "imaging.second_opinion"
