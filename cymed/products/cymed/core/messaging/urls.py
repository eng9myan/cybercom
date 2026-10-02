from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.core.messaging.views import PatientThreadViewSet, StaffThreadViewSet

staff = DefaultRouter()
staff.register(r"threads", StaffThreadViewSet, basename="message-thread")
patient = DefaultRouter()
patient.register(r"threads", PatientThreadViewSet, basename="my-message-thread")

urlpatterns = [
    path("my/", include(patient.urls)),
    path("", include(staff.urls)),
]
