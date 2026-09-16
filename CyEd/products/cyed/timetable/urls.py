from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.timetable.views import TimetableSlotViewSet

router = DefaultRouter()
router.register("slots", TimetableSlotViewSet)

urlpatterns = [path("", include(router.urls))]
