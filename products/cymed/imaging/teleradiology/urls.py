from rest_framework.routers import DefaultRouter
from .views import ReadingQueueViewSet, TeleradiologyCaseViewSet, ReadingAssignmentViewSet, SecondOpinionViewSet

router = DefaultRouter()
router.register("queues", ReadingQueueViewSet, basename="reading-queue")
router.register("cases", TeleradiologyCaseViewSet, basename="teleradiology-case")
router.register("assignments", ReadingAssignmentViewSet, basename="reading-assignment")
router.register("second-opinions", SecondOpinionViewSet, basename="second-opinion")

urlpatterns = router.urls
