from core.viewsets import TenantScopedModelViewSet
from products.cycom.accounting.models import Account, JournalEntry, JournalLine
from products.cycom.accounting.serializers import (
    AccountSerializer,
    JournalEntrySerializer,
    JournalLineSerializer,
)


class AccountViewSet(TenantScopedModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class JournalEntryViewSet(TenantScopedModelViewSet):
    queryset = JournalEntry.objects.prefetch_related("lines").all()
    serializer_class = JournalEntrySerializer


class JournalLineViewSet(TenantScopedModelViewSet):
    queryset = JournalLine.objects.all()
    serializer_class = JournalLineSerializer
