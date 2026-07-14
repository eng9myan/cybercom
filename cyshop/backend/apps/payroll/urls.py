from rest_framework.routers import DefaultRouter
from .views import PayrollBatchViewSet, PayslipViewSet, PayslipLineViewSet

router = DefaultRouter()
router.register(r'batches', PayrollBatchViewSet, basename='payroll-batch')
router.register(r'payslips', PayslipViewSet, basename='payslip')
router.register(r'lines', PayslipLineViewSet, basename='payslip-line')

urlpatterns = router.urls
