from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.commercial.subscriptions.views import (
    SubscriptionPlanViewSet, SubscriptionViewSet, SubscriptionUsageViewSet,
    SubscriptionInvoiceViewSet, SubscriptionContractViewSet
)

router = DefaultRouter()
router.register("plans", SubscriptionPlanViewSet)
router.register("subscriptions", SubscriptionViewSet)
router.register("usage", SubscriptionUsageViewSet)
router.register("invoices", SubscriptionInvoiceViewSet)
router.register("contracts", SubscriptionContractViewSet)

urlpatterns = [path("", include(router.urls))]
