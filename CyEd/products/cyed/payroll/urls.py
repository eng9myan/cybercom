from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.payroll.views import PayrollRunViewSet, PayslipViewSet, SalaryComponentViewSet

router = DefaultRouter()
router.register("runs", PayrollRunViewSet)
router.register("payslips", PayslipViewSet)
router.register("salary-components", SalaryComponentViewSet)

urlpatterns = [path("", include(router.urls))]
