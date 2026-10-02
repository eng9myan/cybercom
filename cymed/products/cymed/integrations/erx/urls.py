from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.integrations.erx import views

router = DefaultRouter()
router.register(r"transmissions", views.ErxTransmissionViewSet, basename="erx-transmission")
router.register(r"pdmp-checks", views.PdmpCheckViewSet, basename="erx-pdmp-check")

urlpatterns = [
    path("transmit/", views.transmit, name="erx-transmit"),
    path("networks/", views.networks, name="erx-networks"),
    path("", include(router.urls)),
]
