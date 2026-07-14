from rest_framework.routers import DefaultRouter

from .views import ModalityViewSet, ModalityWorklistViewSet, StudyQueueViewSet, WorklistEntryViewSet

router = DefaultRouter()
router.register("modalities", ModalityViewSet, basename="modality")
router.register("worklists", ModalityWorklistViewSet, basename="modality-worklist")
router.register("entries", WorklistEntryViewSet, basename="worklist-entry")
router.register("study-queue", StudyQueueViewSet, basename="study-queue")

urlpatterns = router.urls
