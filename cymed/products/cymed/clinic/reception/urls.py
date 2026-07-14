from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.clinic.reception.views import (
    ArrivalMethodViewSet,
    CheckInViewSet,
    CheckOutViewSet,
    PatientQueueTicketViewSet,
    VisitReasonViewSet,
    VisitStatusViewSet,
)

router = DefaultRouter()
router.register("arrival-methods", ArrivalMethodViewSet)
router.register("visit-reasons", VisitReasonViewSet)
router.register("visit-statuses", VisitStatusViewSet)
router.register("checkins", CheckInViewSet)
router.register("checkouts", CheckOutViewSet)
router.register("tickets", PatientQueueTicketViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
