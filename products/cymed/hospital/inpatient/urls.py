from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.hospital.inpatient.views import (
    DailyRoundViewSet,
    DischargePlanningViewSet,
    HospitalStayViewSet,
    InpatientCarePlanViewSet,
    ProgressReviewViewSet,
)

router = DefaultRouter()
router.register("stays", HospitalStayViewSet)
router.register("rounds", DailyRoundViewSet)
router.register("reviews", ProgressReviewViewSet)
router.register("careplans", InpatientCarePlanViewSet)
router.register("discharge-planning", DischargePlanningViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
