from rest_framework.routers import DefaultRouter

from .views import (
    BankAccountViewSet, BankStatementLineViewSet, ReconciliationSessionViewSet,
)

router = DefaultRouter()
router.register(r"accounts", BankAccountViewSet, basename="bank-account")
router.register(r"statement-lines", BankStatementLineViewSet, basename="bank-statement-line")
router.register(r"reconciliations", ReconciliationSessionViewSet, basename="bank-reconciliation")

urlpatterns = router.urls
