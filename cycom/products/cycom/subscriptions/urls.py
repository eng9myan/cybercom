from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.subscriptions.views import SubscriptionPlanViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register("plans", SubscriptionPlanViewSet)
router.register("subscriptions", SubscriptionViewSet)

urlpatterns = [path("", include(router.urls))]
