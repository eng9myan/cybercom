from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.hr.views import (
    ContractViewSet,
    DepartmentViewSet,
    EmployeeDocumentViewSet,
    EmployeeInsuranceViewSet,
    EmployeeViewSet,
)

router = DefaultRouter()
router.register("employees", EmployeeViewSet)
router.register("contracts", ContractViewSet)
router.register("departments", DepartmentViewSet)
router.register("documents", EmployeeDocumentViewSet)
router.register("insurance", EmployeeInsuranceViewSet)

urlpatterns = [path("", include(router.urls))]
