from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.field_service.views import ServiceContractViewSet, ServiceTaskViewSet

router = DefaultRouter()
router.register("tasks", ServiceTaskViewSet)
router.register("contracts", ServiceContractViewSet)

urlpatterns = [path("", include(router.urls))]
