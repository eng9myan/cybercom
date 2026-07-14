from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SystemNotificationViewSet

router = DefaultRouter()
router.register(r'', SystemNotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
