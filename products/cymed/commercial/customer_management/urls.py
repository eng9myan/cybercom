from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.commercial.customer_management.views import (
    CustomerViewSet, CustomerOrganizationViewSet, CustomerContractViewSet,
    CustomerDeploymentViewSet, CustomerSuccessPlanViewSet
)

router = DefaultRouter()
router.register("customers", CustomerViewSet)
router.register("organizations", CustomerOrganizationViewSet)
router.register("contracts", CustomerContractViewSet)
router.register("deployments", CustomerDeploymentViewSet)
router.register("success-plans", CustomerSuccessPlanViewSet)

urlpatterns = [path("", include(router.urls))]
