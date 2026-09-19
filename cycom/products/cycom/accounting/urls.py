from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.accounting.report_views import (
    BalanceSheetView,
    BankReconciliationSummaryView,
    ProfitAndLossView,
    TrialBalanceView,
    VatReturnView,
)
from products.cycom.accounting.views import (
    AccountViewSet,
    BankStatementLineViewSet,
    JournalEntryViewSet,
    JournalLineViewSet,
)

router = DefaultRouter()
router.register("accounts", AccountViewSet)
router.register("journal-entries", JournalEntryViewSet)
router.register("journal-lines", JournalLineViewSet)
router.register("bank-statement-lines", BankStatementLineViewSet)

urlpatterns = [
    path("reports/trial-balance/", TrialBalanceView.as_view(), name="trial-balance"),
    path("reports/profit-and-loss/", ProfitAndLossView.as_view(), name="profit-and-loss"),
    path("reports/balance-sheet/", BalanceSheetView.as_view(), name="balance-sheet"),
    path("reports/vat-return/", VatReturnView.as_view(), name="vat-return"),
    path("reports/bank-reconciliation/", BankReconciliationSummaryView.as_view(), name="bank-reconciliation"),
    path("", include(router.urls)),
]
