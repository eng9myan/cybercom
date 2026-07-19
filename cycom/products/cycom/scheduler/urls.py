from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.scheduler.views import EventViewSet

router = DefaultRouter()
router.register("events", EventViewSet)

urlpatterns = [path("", include(router.urls))]
