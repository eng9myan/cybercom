from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.quality.views import QualityCheckpointViewSet

router = DefaultRouter()
router.register("checkpoints", QualityCheckpointViewSet)

urlpatterns = [path("", include(router.urls))]
