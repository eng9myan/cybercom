from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SystemAuditLogViewSet

router = DefaultRouter()
router.register(r'', SystemAuditLogViewSet, basename='audit')

urlpatterns = [
    path('', include(router.urls)),
]
