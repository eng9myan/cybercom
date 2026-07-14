from rest_framework.routers import DefaultRouter

from .views import DisputeViewSet, PaymentIntentViewSet

router = DefaultRouter()
router.register("intents", PaymentIntentViewSet, basename="payment-intent")
router.register("disputes", DisputeViewSet, basename="dispute")

urlpatterns = router.urls
