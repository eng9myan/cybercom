from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.exams.views import (
    ExamCandidateViewSet,
    ExamRoomAllocationViewSet,
    ExamRoomViewSet,
    ExamSittingViewSet,
)

router = DefaultRouter()
router.register("rooms", ExamRoomViewSet)
router.register("sittings", ExamSittingViewSet)
router.register("room-allocations", ExamRoomAllocationViewSet)
router.register("candidates", ExamCandidateViewSet)

urlpatterns = [path("", include(router.urls))]
