from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"threads", views.MessageThreadViewSet, basename="message-thread")
router.register(r"messages", views.PatientMessageViewSet, basename="patient-message")
router.register(r"attachments", views.MessageAttachmentViewSet, basename="message-attachment")
router.register(r"recipients", views.SecureMessageRecipientViewSet, basename="message-recipient")

urlpatterns = [
    path("", include(router.urls)),
]
