from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.field_service.views import ServiceTaskViewSet

router = DefaultRouter()
router.register("tasks", ServiceTaskViewSet)

urlpatterns = [path("", include(router.urls))]
