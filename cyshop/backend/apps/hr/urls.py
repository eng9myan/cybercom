from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, ContractViewSet, LeaveTypeViewSet, LeaveRequestViewSet

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'contracts', ContractViewSet, basename='contract')
router.register(r'leave-types', LeaveTypeViewSet, basename='leave-type')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leave-request')

urlpatterns = router.urls
