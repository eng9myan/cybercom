from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.payments.views import PaymentIntentViewSet, WebhookEventViewSet

router = DefaultRouter()
router.register("intents", PaymentIntentViewSet)
router.register("webhook-events", WebhookEventViewSet)

urlpatterns = [path("", include(router.urls))]

# The gateway callback is NOT here — it carries neither a bearer token nor a
# tenant header, so it is mounted under /api/v1/public/ instead. See
# products/cyed/payments/public_urls.py.
