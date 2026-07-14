from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(
    r"sessions",
    views.TelemedicineSessionViewSet,
    basename="portal-telemedicine-session",
)
router.register(
    r"documents",
    views.TelemedicineDocumentViewSet,
    basename="portal-telemedicine-document",
)
router.register(
    r"chat",
    views.TelemedicineChatViewSet,
    basename="portal-telemedicine-chat",
)
router.register(
    r"ratings",
    views.TelemedicineRatingViewSet,
    basename="portal-telemedicine-rating",
)

urlpatterns = [path("", include(router.urls))]
