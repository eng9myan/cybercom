from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.core.registries.views import CohortRegistryViewSet, RegistryEntryViewSet

router = DefaultRouter()
router.register(r"entries", RegistryEntryViewSet, basename="registry-entry")
router.register(r"", CohortRegistryViewSet, basename="cohort-registry")

urlpatterns = [
    path("", include(router.urls)),
]
