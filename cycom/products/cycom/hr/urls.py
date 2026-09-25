from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.hr.views import (
    ContractViewSet,
    EmployeeDocumentViewSet,
    EmployeeInsuranceViewSet,
    EmployeeViewSet,
)

router = DefaultRouter()
router.register("employees", EmployeeViewSet)
router.register("contracts", ContractViewSet)
router.register("documents", EmployeeDocumentViewSet)
router.register("insurance", EmployeeInsuranceViewSet)

urlpatterns = [path("", include(router.urls))]
