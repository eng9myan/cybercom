from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.core.providers.views import ProviderViewSet

router = DefaultRouter()
router.register(r"", ProviderViewSet, basename="provider")

urlpatterns = [
    path("", include(router.urls)),
]
