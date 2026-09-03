from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.planning.views import ShiftSlotViewSet

router = DefaultRouter()
router.register("slots", ShiftSlotViewSet)

urlpatterns = [path("", include(router.urls))]
