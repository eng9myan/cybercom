from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("runs", views.PayrollRunViewSet, basename="payroll-run")
router.register("payslips", views.PayslipViewSet, basename="payslip")

urlpatterns = router.urls
