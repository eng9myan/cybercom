from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.docai.views import ParsedDocumentViewSet

router = DefaultRouter()
router.register("documents", ParsedDocumentViewSet, basename="docai-document")

urlpatterns = [
    path("", include(router.urls)),
]
