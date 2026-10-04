from rest_framework.routers import DefaultRouter

from .views import EphemeralEnvironmentViewSet

router = DefaultRouter()
router.register(r"", EphemeralEnvironmentViewSet, basename="ephemeral-environment")

urlpatterns = router.urls
