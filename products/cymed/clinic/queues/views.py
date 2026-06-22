from products.cymed.clinic.views import ClinicModelViewSet
from products.cymed.clinic.queues.models import Queue, QueueEntry, QueueBoard, ProviderQueue
from products.cymed.clinic.queues.serializers import (
    QueueSerializer, QueueEntrySerializer, QueueBoardSerializer, ProviderQueueSerializer
)

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

