from rest_framework.routers import DefaultRouter

from products.cyed.docsign.views import (
    SignableDocumentViewSet, SignatoryViewSet, SignatureAuditEventViewSet,
)

router = DefaultRouter()
router.register("documents", SignableDocumentViewSet, basename="signable-document")
router.register("signatories", SignatoryViewSet, basename="signatory")
router.register("audit-events", SignatureAuditEventViewSet, basename="signature-audit-event")

urlpatterns = router.urls
