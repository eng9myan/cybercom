from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.events.views import EventViewSet, RegistrationViewSet, TicketTypeViewSet

router = DefaultRouter()
router.register("events", EventViewSet)
router.register("ticket-types", TicketTypeViewSet)
router.register("registrations", RegistrationViewSet)

urlpatterns = [path("", include(router.urls))]
