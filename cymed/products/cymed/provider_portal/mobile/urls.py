from rest_framework.routers import DefaultRouter

from .views import (
    MobilePreferencesViewSet,
    MobilePushNotificationViewSet,
    MobileSessionViewSet,
    ProviderMobileDeviceViewSet,
)

router = DefaultRouter()
router.register(
    r"devices",
    ProviderMobileDeviceViewSet,
    basename="mobile-device",
)
router.register(
    r"sessions",
    MobileSessionViewSet,
    basename="mobile-session",
)
router.register(
    r"preferences",
    MobilePreferencesViewSet,
    basename="mobile-preferences",
)
router.register(
    r"notifications",
    MobilePushNotificationViewSet,
    basename="mobile-notification",
)

urlpatterns = router.urls
