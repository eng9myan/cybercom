from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Account, Journal, JournalEntry, JournalEntryLine, FiscalPeriod
from .serializers import (
    AccountSerializer,
    JournalSerializer,
    JournalEntrySerializer,
    JournalEntryLineSerializer,
    FiscalPeriodSerializer,
)


class AccountViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AccountSerializer

    def get_queryset(self):
        qs = Account.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        )
        account_type = self.request.query_params.get('account_type')
        if account_type:
            qs = qs.filter(account_type=account_type)
        parent = self.request.query_params.get('parent')
        if parent:
            qs = qs.filter(parent=parent)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('1', 'true'))
        return qs.select_related('parent')


class JournalViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = JournalSerializer

    def get_queryset(self):
        qs = Journal.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        )
        journal_type = self.request.query_params.get('journal_type')
        if journal_type:
            qs = qs.filter(journal_type=journal_type)
        return qs


class JournalEntryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = JournalEntrySerializer

    def get_queryset(self):
        qs = JournalEntry.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        )
        journal = self.request.query_params.get('journal')
        if journal:
            qs = qs.filter(journal=journal)
        entry_status = self.request.query_params.get('status')
        if entry_status:
            qs = qs.filter(status=entry_status)
        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(entry_date__gte=date_from)
        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(entry_date__lte=date_to)
        return qs.select_related('journal').prefetch_related('lines__account')

    @action(detail=True, methods=['post'])
    def post_entry(self, request, pk=None):
        """Validate that debits == credits, then set status to 'posted'."""
        entry = self.get_object()

        if entry.status == 'posted':
            return Response(
                {'error': 'Entry is already posted.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if entry.status == 'cancelled':
            return Response(
                {'error': 'Cancelled entries cannot be posted.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not entry.lines.exists():
            return Response(
                {'error': 'Cannot post an entry with no lines.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not entry.is_balanced:
            return Response(
                {'error': 'Entry is not balanced: total debits must equal total credits.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        entry.status = 'posted'
        entry.save(update_fields=['status', 'updated_at', 'version'])
        serializer = self.get_serializer(entry)
        return Response(serializer.data, status=status.HTTP_200_OK)


class JournalEntryLineViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = JournalEntryLineSerializer

    def get_queryset(self):
        qs = JournalEntryLine.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        )
        entry = self.request.query_params.get('entry')
        if entry:
            qs = qs.filter(entry=entry)
        account = self.request.query_params.get('account')
        if account:
            qs = qs.filter(account=account)
        return qs.select_related('entry', 'account')


class FiscalPeriodViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FiscalPeriodSerializer

    def get_queryset(self):
        qs = FiscalPeriod.objects.filter(
            tenant_id=self.request.tenant_id, is_deleted=False
        )
        period_status = self.request.query_params.get('status')
        if period_status:
            qs = qs.filter(status=period_status)
        return qs

    @action(detail=True, methods=['post'])
    def close_period(self, request, pk=None):
        """Close an open fiscal period."""
        period = self.get_object()
        if period.status == 'closed':
            return Response(
                {'error': 'Period is already closed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        period.status = 'closed'
        period.save(update_fields=['status', 'updated_at', 'version'])
        return Response(FiscalPeriodSerializer(period, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def reopen_period(self, request, pk=None):
        """Re-open a closed fiscal period."""
        period = self.get_object()
        if period.status == 'open':
            return Response(
                {'error': 'Period is already open.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        period.status = 'open'
        period.save(update_fields=['status', 'updated_at', 'version'])
        return Response(FiscalPeriodSerializer(period, context={'request': request}).data)
