from django.urls import path
from .views import (
    NotificationListView, NotificationDetailView,
    NotificationSendFromTemplateView, TemplateListView, TemplateDetailView,
)

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("<uuid:pk>/", NotificationDetailView.as_view(), name="notification-detail"),
    path("send-from-template/", NotificationSendFromTemplateView.as_view(), name="notification-from-template"),
    path("templates/", TemplateListView.as_view(), name="notification-template-list"),
    path("templates/<uuid:pk>/", TemplateDetailView.as_view(), name="notification-template-detail"),
]
