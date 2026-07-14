from products.cymed.imaging.views import ImagingModelViewSet

from .models import Modality, ModalityWorklist, StudyQueue, WorklistEntry
from .serializers import (
    ModalitySerializer,
    ModalityWorklistSerializer,
    StudyQueueSerializer,
    WorklistEntrySerializer,
)


class ModalityViewSet(ImagingModelViewSet):
    queryset = Modality.objects.all()
    serializer_class = ModalitySerializer
    required_feature = "imaging.worklist"


class ModalityWorklistViewSet(ImagingModelViewSet):
    queryset = ModalityWorklist.objects.select_related("modality").prefetch_related("entries")
    serializer_class = ModalityWorklistSerializer
    required_feature = "imaging.worklist"


class WorklistEntryViewSet(ImagingModelViewSet):
    queryset = WorklistEntry.objects.select_related("worklist", "order_item")
    serializer_class = WorklistEntrySerializer
    required_feature = "imaging.worklist"


class StudyQueueViewSet(ImagingModelViewSet):
    queryset = StudyQueue.objects.select_related("order_item")
    serializer_class = StudyQueueSerializer
    required_feature = "imaging.worklist"
