from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.core.consents.views import ConsentViewSet

router = DefaultRouter()
router.register(r"", ConsentViewSet, basename="consent")

urlpatterns = [
    path("", include(router.urls)),
]
