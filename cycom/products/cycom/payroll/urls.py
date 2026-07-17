from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.payroll.views import AttendanceRecordViewSet, PayrollRunViewSet

router = DefaultRouter()
router.register("attendance", AttendanceRecordViewSet)
router.register("runs", PayrollRunViewSet)

urlpatterns = [path("", include(router.urls))]
