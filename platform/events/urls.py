from django.urls import include, path
from rest_framework.routers import DefaultRouter

from platform.events.views import (
    DeadLetterEventViewSet,
    EventDeliveryLogViewSet,
    OutboxEventViewSet,
)

router = DefaultRouter()
router.register("outbox", OutboxEventViewSet, basename="event-outbox")
router.register("dlq", DeadLetterEventViewSet, basename="event-dlq")
router.register("delivery-logs", EventDeliveryLogViewSet, basename="event-delivery-log")

urlpatterns = [
    path("", include(router.urls)),
]
