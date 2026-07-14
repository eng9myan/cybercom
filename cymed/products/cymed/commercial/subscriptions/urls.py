from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.commercial.subscriptions.views import (
    SubscriptionContractViewSet,
    SubscriptionInvoiceViewSet,
    SubscriptionPlanViewSet,
    SubscriptionUsageViewSet,
    SubscriptionViewSet,
)

router = DefaultRouter()
router.register("plans", SubscriptionPlanViewSet)
router.register("subscriptions", SubscriptionViewSet)
router.register("usage", SubscriptionUsageViewSet)
router.register("invoices", SubscriptionInvoiceViewSet)
router.register("contracts", SubscriptionContractViewSet)

urlpatterns = [path("", include(router.urls))]
