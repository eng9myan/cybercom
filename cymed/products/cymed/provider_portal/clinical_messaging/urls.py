from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.provider_portal.clinical_messaging.views import (
    ClinicalGroupViewSet,
    ClinicalMessageThreadViewSet,
    ClinicalMessageViewSet,
    MessageAttachmentViewSet,
    MessageThreadParticipantViewSet,
)

router = DefaultRouter()
router.register(r"threads", ClinicalMessageThreadViewSet, basename="clinical-message-thread")
router.register(r"messages", ClinicalMessageViewSet, basename="clinical-message")
router.register(r"attachments", MessageAttachmentViewSet, basename="message-attachment")
router.register(r"groups", ClinicalGroupViewSet, basename="clinical-group")
router.register(r"participants", MessageThreadParticipantViewSet, basename="thread-participant")

urlpatterns = [
    path("", include(router.urls)),
]
