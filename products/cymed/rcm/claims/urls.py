from rest_framework.routers import DefaultRouter

from .views import (
    ClaimAttachmentViewSet,
    ClaimLineViewSet,
    ClaimResponseViewSet,
    ClaimStatusViewSet,
    ClaimSubmissionViewSet,
    ClaimViewSet,
)

router = DefaultRouter()
router.register(r"", ClaimViewSet, basename="claim")
router.register(r"lines", ClaimLineViewSet, basename="claim-line")
router.register(r"submissions", ClaimSubmissionViewSet, basename="claim-submission")
router.register(r"responses", ClaimResponseViewSet, basename="claim-response")
router.register(r"status-history", ClaimStatusViewSet, basename="claim-status")
router.register(r"attachments", ClaimAttachmentViewSet, basename="claim-attachment")

urlpatterns = router.urls
