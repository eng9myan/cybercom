from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.substitution.views import (
    ReliefAvailabilityViewSet,
    ReliefBookingViewSet,
    ReliefTeacherViewSet,
    SubstitutionAssignmentViewSet,
    SubstitutionPlanViewSet,
)

router = DefaultRouter()
router.register("plans", SubstitutionPlanViewSet)
router.register("assignments", SubstitutionAssignmentViewSet)
router.register("relief-teachers", ReliefTeacherViewSet)
router.register("relief-availability", ReliefAvailabilityViewSet)
router.register("relief-bookings", ReliefBookingViewSet)

urlpatterns = [path("", include(router.urls))]
