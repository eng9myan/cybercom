from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    AccountViewSet,
    JournalViewSet,
    JournalEntryViewSet,
    JournalEntryLineViewSet,
    FiscalPeriodViewSet,
)
from .reports import TrialBalanceView, IncomeStatementView, BalanceSheetView

router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'journals', JournalViewSet, basename='journal')
router.register(r'entries', JournalEntryViewSet, basename='journal-entry')
router.register(r'entry-lines', JournalEntryLineViewSet, basename='journal-entry-line')
router.register(r'fiscal-periods', FiscalPeriodViewSet, basename='fiscal-period')

urlpatterns = router.urls + [
    path('reports/trial-balance/', TrialBalanceView.as_view(), name='trial-balance'),
    path('reports/income-statement/', IncomeStatementView.as_view(), name='income-statement'),
    path('reports/balance-sheet/', BalanceSheetView.as_view(), name='balance-sheet'),
]
