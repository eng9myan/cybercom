from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.core.facilities.views import FacilityViewSet

router = DefaultRouter()
router.register(r"", FacilityViewSet, basename="facility")

urlpatterns = [
    path("", include(router.urls)),
]
