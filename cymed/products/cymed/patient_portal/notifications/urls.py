from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"notifications", views.PatientNotificationViewSet, basename="notification")
router.register(
    r"preferences", views.NotificationPreferenceViewSet, basename="notification-preference"
)
router.register(r"templates", views.NotificationTemplateViewSet, basename="notification-template")
router.register(r"push-subscriptions", views.PushSubscriptionViewSet, basename="push-subscription")

urlpatterns = [
    path("", include(router.urls)),
]
