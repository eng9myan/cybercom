from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.cyai_memory.views import MemoryQueryLogViewSet, QueryPlanViewSet

router = DefaultRouter()
router.register("plans", QueryPlanViewSet)
router.register("logs", MemoryQueryLogViewSet)

urlpatterns = [path("", include(router.urls))]
