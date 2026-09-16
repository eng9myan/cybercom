from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.billing.views import (
    BillLineItemViewSet,
    CreditNoteViewSet,
    DunningCaseViewSet,
    FamilyAccountViewSet,
    FeePlanViewSet,
    InstallmentPaymentViewSet,
    InstallmentViewSet,
    SiblingDiscountRuleViewSet,
    StudentBillViewSet,
)

router = DefaultRouter()
router.register("plans", FeePlanViewSet)
router.register("bills", StudentBillViewSet)
router.register("line-items", BillLineItemViewSet)
router.register("installments", InstallmentViewSet)
router.register("payments", InstallmentPaymentViewSet)
router.register("sibling-discounts", SiblingDiscountRuleViewSet)
router.register("credit-notes", CreditNoteViewSet)
router.register("dunning-cases", DunningCaseViewSet)
# Household money view: consolidated statement + dunning worklist. Basename is
# explicit because the queryset is sis.Family, not a billing model.
router.register("families", FamilyAccountViewSet, basename="family-account")

urlpatterns = [path("", include(router.urls))]
