from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.accounting.report_views import (
    BalanceSheetView,
    ProfitAndLossView,
    TrialBalanceView,
    VatReturnView,
)
from products.cycom.accounting.views import AccountViewSet, JournalEntryViewSet, JournalLineViewSet

router = DefaultRouter()
router.register("accounts", AccountViewSet)
router.register("journal-entries", JournalEntryViewSet)
router.register("journal-lines", JournalLineViewSet)

urlpatterns = [
    path("reports/trial-balance/", TrialBalanceView.as_view(), name="trial-balance"),
    path("reports/profit-and-loss/", ProfitAndLossView.as_view(), name="profit-and-loss"),
    path("reports/balance-sheet/", BalanceSheetView.as_view(), name="balance-sheet"),
    path("reports/vat-return/", VatReturnView.as_view(), name="vat-return"),
    path("", include(router.urls)),
]
