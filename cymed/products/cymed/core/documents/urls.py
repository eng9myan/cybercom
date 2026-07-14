from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.core.documents.views import ClinicalDocumentViewSet

router = DefaultRouter()
router.register(r"", ClinicalDocumentViewSet, basename="document")

urlpatterns = [
    path("", include(router.urls)),
]
