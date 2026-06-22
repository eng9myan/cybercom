from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.core.careplans.views import CarePlanViewSet

router = DefaultRouter()
router.register(r"", CarePlanViewSet, basename="careplan")

urlpatterns = [
    path("", include(router.urls)),
]
