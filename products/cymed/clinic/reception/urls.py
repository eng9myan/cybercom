from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.clinic.reception.views import (
    ArrivalMethodViewSet, VisitReasonViewSet, VisitStatusViewSet,
    CheckInViewSet, CheckOutViewSet, PatientQueueTicketViewSet
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
