from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.maintenance.views import EquipmentViewSet, MaintenanceRequestViewSet

router = DefaultRouter()
router.register("equipment", EquipmentViewSet)
router.register("requests", MaintenanceRequestViewSet)

urlpatterns = [path("", include(router.urls))]
