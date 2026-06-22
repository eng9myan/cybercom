from django.urls import path, include
from rest_framework.routers import DefaultRouter
from platform.events.views import OutboxEventViewSet, DeadLetterEventViewSet, EventDeliveryLogViewSet

router = DefaultRouter()
router.register("outbox", OutboxEventViewSet, basename="event-outbox")
router.register("dlq", DeadLetterEventViewSet, basename="event-dlq")
router.register("delivery-logs", EventDeliveryLogViewSet, basename="event-delivery-log")

urlpatterns = [
    path("", include(router.urls)),
]
