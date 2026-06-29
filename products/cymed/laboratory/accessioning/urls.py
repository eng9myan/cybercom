from rest_framework.routers import DefaultRouter

from .views import AccessionAuditViewSet, AccessionBatchViewSet, AccessionViewSet

router = DefaultRouter()
router.register("accessions", AccessionViewSet, basename="lab-accessions")
router.register("batches", AccessionBatchViewSet, basename="lab-accession-batches")
router.register("audit", AccessionAuditViewSet, basename="lab-accession-audit")

urlpatterns = router.urls
