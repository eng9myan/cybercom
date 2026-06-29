from rest_framework.routers import DefaultRouter

from .views import (
    AgencyStaffRegistrationViewSet,
    FloatDeploymentViewSet,
    FloatPoolMemberViewSet,
    StaffingShortageAlertViewSet,
)

router = DefaultRouter()
router.register("members", FloatPoolMemberViewSet, basename="float-pool-member")
router.register("deployments", FloatDeploymentViewSet, basename="float-deployment")
router.register("agency-staff", AgencyStaffRegistrationViewSet, basename="agency-staff")
router.register("shortage-alerts", StaffingShortageAlertViewSet, basename="shortage-alert")

urlpatterns = router.urls
