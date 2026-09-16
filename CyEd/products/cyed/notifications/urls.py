from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.notifications.bulk_views import NewsletterViewSet, PushDeviceViewSet
from products.cyed.notifications.views import NotificationViewSet

# Order matters. `NotificationViewSet` is mounted at the empty prefix, so its
# detail route matches any single path segment — `/newsletters/` would be read
# as a notification with pk="newsletters". The named prefixes are registered
# first so they win.
router = DefaultRouter()
router.register("newsletters", NewsletterViewSet)
router.register("devices", PushDeviceViewSet)
router.register("", NotificationViewSet, basename="notification")

urlpatterns = [path("", include(router.urls))]
