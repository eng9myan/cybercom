from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.payroll.views import (
    AttendanceRecordViewSet,
    PayrollRunViewSet,
    PayslipViewSet,
)

router = DefaultRouter()
router.register("attendance", AttendanceRecordViewSet)
router.register("runs", PayrollRunViewSet)
router.register("payslips", PayslipViewSet, basename="payslip")

urlpatterns = [path("", include(router.urls))]
