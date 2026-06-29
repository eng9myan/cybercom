from rest_framework.routers import DefaultRouter

from .views import (
    LabOrderAttachmentViewSet,
    LabOrderDiagnosisViewSet,
    LabOrderItemViewSet,
    LabOrderViewSet,
    LabPanelViewSet,
    LabTestViewSet,
)

router = DefaultRouter()
router.register("tests", LabTestViewSet, basename="lab-tests")
router.register("panels", LabPanelViewSet, basename="lab-panels")
router.register("orders", LabOrderViewSet, basename="lab-orders")
router.register("order-items", LabOrderItemViewSet, basename="lab-order-items")
router.register("order-diagnoses", LabOrderDiagnosisViewSet, basename="lab-order-diagnoses")
router.register("order-attachments", LabOrderAttachmentViewSet, basename="lab-order-attachments")

urlpatterns = router.urls
