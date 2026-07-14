from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.hospital.adt.views import (
    AdmissionReasonViewSet,
    AdmissionTypeViewSet,
    AdmissionViewSet,
    DischargeDispositionViewSet,
    DischargeReasonViewSet,
    DischargeSummaryViewSet,
    TransferApprovalViewSet,
    TransferRequestViewSet,
)

router = DefaultRouter()
router.register("reasons", AdmissionReasonViewSet)
router.register("types", AdmissionTypeViewSet)
router.register("discharge-reasons", DischargeReasonViewSet)
router.register("dispositions", DischargeDispositionViewSet)
router.register("admissions", AdmissionViewSet)
router.register("transfer-requests", TransferRequestViewSet)
router.register("transfer-approvals", TransferApprovalViewSet)
router.register("discharge-summaries", DischargeSummaryViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
