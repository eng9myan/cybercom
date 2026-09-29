from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.accounting.report_views import (
    BalanceSheetView,
    BankReconciliationSummaryView,
    BudgetVsActualView,
    CashFlowStatementView,
    ProfitAndLossView,
    TrialBalanceView,
    VatReturnView,
)
from products.cycom.accounting.mtd_views import (
    MtdCallbackView,
    MtdConnectView,
    MtdDisconnectView,
    MtdObligationsView,
    MtdPreviewView,
    MtdStatusView,
    MtdSubmissionsView,
    MtdSubmitView,
)
from products.cycom.accounting.saft_views import SaftExportView, SaftSettingsView
from products.cycom.accounting.views import (
    AccountViewSet,
    BankStatementLineViewSet,
    BudgetViewSet,
    FixedAssetViewSet,
    JournalEntryViewSet,
    JournalLineViewSet,
)

router = DefaultRouter()
router.register("accounts", AccountViewSet)
router.register("journal-entries", JournalEntryViewSet)
router.register("journal-lines", JournalLineViewSet)
router.register("bank-statement-lines", BankStatementLineViewSet)
router.register("fixed-assets", FixedAssetViewSet)
router.register("budgets", BudgetViewSet)

urlpatterns = [
    path("mtd/status/", MtdStatusView.as_view(), name="mtd-status"),
    path("mtd/connect/", MtdConnectView.as_view(), name="mtd-connect"),
    path("mtd/callback/", MtdCallbackView.as_view(), name="mtd-callback"),
    path("mtd/disconnect/", MtdDisconnectView.as_view(), name="mtd-disconnect"),
    path("mtd/obligations/", MtdObligationsView.as_view(), name="mtd-obligations"),
    path("mtd/preview/", MtdPreviewView.as_view(), name="mtd-preview"),
    path("mtd/submit/", MtdSubmitView.as_view(), name="mtd-submit"),
    path("mtd/submissions/", MtdSubmissionsView.as_view(), name="mtd-submissions"),
    path("saft/settings/", SaftSettingsView.as_view(), name="saft-settings"),
    path("saft/export/", SaftExportView.as_view(), name="saft-export"),
    path("reports/trial-balance/", TrialBalanceView.as_view(), name="trial-balance"),
    path("reports/profit-and-loss/", ProfitAndLossView.as_view(), name="profit-and-loss"),
    path("reports/balance-sheet/", BalanceSheetView.as_view(), name="balance-sheet"),
    path("reports/vat-return/", VatReturnView.as_view(), name="vat-return"),
    path("reports/cash-flow/", CashFlowStatementView.as_view(), name="cash-flow-statement"),
    path("reports/budget-vs-actual/<uuid:pk>/", BudgetVsActualView.as_view(), name="budget-vs-actual"),
    path("reports/bank-reconciliation/", BankReconciliationSummaryView.as_view(), name="bank-reconciliation"),
    path("", include(router.urls)),
]
