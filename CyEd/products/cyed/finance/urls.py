from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.finance.views import (
    AccountViewSet,
    ArAgingView,
    BalanceSheetView,
    BasReportView,
    BankStatementLineViewSet,
    BankStatementViewSet,
    BudgetLineViewSet,
    BudgetViewSet,
    JournalEntryViewSet,
    ProfitAndLossView,
    TrialBalanceView,
)

router = DefaultRouter()
router.register("accounts", AccountViewSet)
router.register("journal-entries", JournalEntryViewSet)
router.register("budgets", BudgetViewSet)
router.register("budget-lines", BudgetLineViewSet)
router.register("bank-statements", BankStatementViewSet)
router.register("bank-lines", BankStatementLineViewSet)

urlpatterns = [
    path("trial-balance/", TrialBalanceView.as_view(), name="trial-balance"),
    path("profit-and-loss/", ProfitAndLossView.as_view(), name="profit-and-loss"),
    path("balance-sheet/", BalanceSheetView.as_view(), name="balance-sheet"),
    path("bas/", BasReportView.as_view(), name="bas-report"),
    path("ar-aging/", ArAgingView.as_view(), name="ar-aging"),
    path("", include(router.urls)),
]
