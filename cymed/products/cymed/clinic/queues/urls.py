from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.clinic.queues.views import (
    ProviderQueueViewSet,
    QueueBoardViewSet,
    QueueEntryViewSet,
    QueueViewSet,
)

router = DefaultRouter()
router.register("boards", QueueBoardViewSet)
router.register("provider-queues", ProviderQueueViewSet)
router.register("entries", QueueEntryViewSet)
router.register("queues", QueueViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
