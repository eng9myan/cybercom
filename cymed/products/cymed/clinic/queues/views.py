from products.cymed.clinic.queues.models import ProviderQueue, Queue, QueueBoard, QueueEntry
from products.cymed.clinic.queues.serializers import (
    ProviderQueueSerializer,
    QueueBoardSerializer,
    QueueEntrySerializer,
    QueueSerializer,
)
from products.cymed.clinic.views import ClinicModelViewSet


class QueueViewSet(ClinicModelViewSet):
    queryset = Queue.objects.all()
    serializer_class = QueueSerializer


class QueueEntryViewSet(ClinicModelViewSet):
    queryset = QueueEntry.objects.all().order_by("-priority_level")
    serializer_class = QueueEntrySerializer


class QueueBoardViewSet(ClinicModelViewSet):
    queryset = QueueBoard.objects.all()
    serializer_class = QueueBoardSerializer


class ProviderQueueViewSet(ClinicModelViewSet):
    queryset = ProviderQueue.objects.all()
    serializer_class = ProviderQueueSerializer
