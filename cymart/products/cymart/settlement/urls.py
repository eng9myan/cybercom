from rest_framework.routers import DefaultRouter

from .views import SettlementLedgerEntryViewSet

router = DefaultRouter()
router.register("ledger", SettlementLedgerEntryViewSet, basename="settlement-ledger")

urlpatterns = router.urls
