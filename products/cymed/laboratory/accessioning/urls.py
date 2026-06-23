from rest_framework.routers import DefaultRouter
from .views import AccessionViewSet, AccessionBatchViewSet, AccessionAuditViewSet

router = DefaultRouter()
router.register("accessions", AccessionViewSet, basename="lab-accessions")
router.register("batches", AccessionBatchViewSet, basename="lab-accession-batches")
router.register("audit", AccessionAuditViewSet, basename="lab-accession-audit")

urlpatterns = router.urls
