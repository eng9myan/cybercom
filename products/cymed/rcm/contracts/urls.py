from rest_framework.routers import DefaultRouter
from .views import (
    PayerContractViewSet, ContractRateViewSet,
    ContractRuleViewSet, ReimbursementRuleViewSet,
)

router = DefaultRouter()
router.register(r"", PayerContractViewSet, basename="payer-contract")
router.register(r"rates", ContractRateViewSet, basename="contract-rate")
router.register(r"rules", ContractRuleViewSet, basename="contract-rule")
router.register(r"reimbursement-rules", ReimbursementRuleViewSet, basename="reimbursement-rule")

urlpatterns = router.urls
