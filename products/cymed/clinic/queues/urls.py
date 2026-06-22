from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.clinic.queues.views import (
    QueueViewSet, QueueEntryViewSet, QueueBoardViewSet, ProviderQueueViewSet
)

router = DefaultRouter()
router.register("boards", QueueBoardViewSet)
router.register("provider-queues", ProviderQueueViewSet)
router.register("entries", QueueEntryViewSet)
router.register("queues", QueueViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
