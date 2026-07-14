from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"sessions", views.ProviderTelemedicineSessionViewSet, basename="tele-session")
router.register(r"consult-requests", views.ConsultRequestViewSet, basename="consult-request")
router.register(r"second-opinions", views.SecondOpinionRequestViewSet, basename="second-opinion")
router.register(r"documents", views.TelemedicineDocumentViewSet, basename="tele-document")

urlpatterns = [path("", include(router.urls))]
