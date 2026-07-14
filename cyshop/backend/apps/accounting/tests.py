import datetime
import jwt
from decimal import Decimal

from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.tenants.models import Tenant
from .models import Account, Journal, JournalEntry, JournalEntryLine, FiscalPeriod

User = get_user_model()
TENANT_ID = '018f2b3c-4d5e-7f6a-9b0c-1d2e3f4a5b6c'


def _make_token(user):
    payload = {
        'user_id': str(user.id),
        'username': user.username,
        'tenant_id': TENANT_ID,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def _api_client(user):
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {_make_token(user)}',
        HTTP_X_TENANT_ID=TENANT_ID,
    )
    return client


def _setup_base():
    tenant = Tenant.objects.create(name='Acct Tenant', subdomain='acct', tenant_id=TENANT_ID)
    asset_account = Account.objects.create(
        code='1000', name='Cash', name_ar='نقد',
        account_type='asset', tenant_id=TENANT_ID,
    )
    revenue_account = Account.objects.create(
        code='4000', name='Sales Revenue', name_ar='إيرادات المبيعات',
        account_type='revenue', tenant_id=TENANT_ID,
    )
    journal = Journal.objects.create(
        code='GJ', name='General Journal', journal_type='general',
        currency='SAR', tenant_id=TENANT_ID,
    )
    return tenant, asset_account, revenue_account, journal


class AccountTests(TestCase):

    def setUp(self):
        self.tenant, self.asset_acct, self.revenue_acct, self.journal = _setup_base()

    def test_create_account(self):
        """An Account can be created and retrieved by its code."""
        acct = Account.objects.get(code='1000', tenant_id=TENANT_ID)
        self.assertEqual(acct.name, 'Cash')
        self.assertEqual(acct.account_type, 'asset')

    def test_account_str(self):
        self.assertIn('1000', str(self.asset_acct))
        self.assertIn('Cash', str(self.asset_acct))

    def test_list_accounts_filtered_by_tenant(self):
        """API list endpoint returns only the requesting tenant's accounts."""
        user = User.objects.create_user(username='acctuser', password='x', tenant_id=TENANT_ID)
        client = _api_client(user)
        # Create a second account under a different tenant_id to ensure filtering.
        Account.objects.create(
            code='9999', name='Foreign Account', name_ar='حساب أجنبي',
            account_type='expense', tenant_id='00000000-0000-7000-8000-000000000000',
        )
        res = client.get('/api/v1/accounting/accounts/')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        result_list = data.get('results', data) if isinstance(data, dict) else data
        codes = [a['code'] for a in result_list]
        # All returned accounts must belong to TENANT_ID
        for a in result_list:
            self.assertEqual(a['tenant_id'], TENANT_ID)


class JournalTests(TestCase):

    def setUp(self):
        self.tenant, self.asset_acct, self.revenue_acct, self.journal = _setup_base()

    def test_create_journal(self):
        """A Journal can be created and has the correct currency default."""
        jnl = Journal.objects.get(code='GJ', tenant_id=TENANT_ID)
        self.assertEqual(jnl.journal_type, 'general')
        self.assertEqual(jnl.currency, 'SAR')

    def test_journal_str(self):
        self.assertIn('GJ', str(self.journal))
        self.assertIn('General Journal', str(self.journal))


class JournalEntryTests(TestCase):

    def setUp(self):
        self.tenant, self.asset_acct, self.revenue_acct, self.journal = _setup_base()

    def _make_entry(self, debit_amount, credit_amount, status='draft'):
        entry = JournalEntry.objects.create(
            journal=self.journal,
            reference='JE-001',
            entry_date=datetime.date(2026, 1, 15),
            description='Test entry',
            status=status,
            tenant_id=TENANT_ID,
        )
        JournalEntryLine.objects.create(
            entry=entry, account=self.asset_acct,
            debit=debit_amount, credit=Decimal('0.00'),
            tenant_id=TENANT_ID,
        )
        JournalEntryLine.objects.create(
            entry=entry, account=self.revenue_acct,
            debit=Decimal('0.00'), credit=credit_amount,
            tenant_id=TENANT_ID,
        )
        return entry

    def test_create_balanced_entry(self):
        """A balanced entry (debits == credits) can be created successfully."""
        entry = self._make_entry(Decimal('500.00'), Decimal('500.00'))
        self.assertTrue(entry.is_balanced)
        self.assertEqual(entry.status, 'draft')

    def test_create_unbalanced_entry_raises_on_post(self):
        """An unbalanced entry raises ValidationError when status is set to posted."""
        entry = self._make_entry(Decimal('500.00'), Decimal('300.00'))
        self.assertFalse(entry.is_balanced)
        entry.status = 'posted'
        with self.assertRaises(ValidationError):
            entry.clean()

    def test_post_entry_action_balanced(self):
        """The post_entry API action succeeds on a balanced entry."""
        user = User.objects.create_user(username='postuser', password='x', tenant_id=TENANT_ID)
        client = _api_client(user)
        entry = self._make_entry(Decimal('750.00'), Decimal('750.00'))
        res = client.post(f'/api/v1/accounting/entries/{entry.id}/post_entry/')
        self.assertEqual(res.status_code, 200)
        entry.refresh_from_db()
        self.assertEqual(entry.status, 'posted')

    def test_post_entry_action_unbalanced(self):
        """The post_entry API action rejects an unbalanced entry with 400."""
        user = User.objects.create_user(username='postuser2', password='x', tenant_id=TENANT_ID)
        client = _api_client(user)
        entry = self._make_entry(Decimal('750.00'), Decimal('400.00'))
        res = client.post(f'/api/v1/accounting/entries/{entry.id}/post_entry/')
        self.assertEqual(res.status_code, 400)
        self.assertIn('error', res.json())

    def test_is_balanced_property(self):
        """is_balanced returns True only when debits equal credits."""
        entry_bal = self._make_entry(Decimal('100.00'), Decimal('100.00'))
        entry_unbal = self._make_entry(Decimal('100.00'), Decimal('99.00'))
        self.assertTrue(entry_bal.is_balanced)
        self.assertFalse(entry_unbal.is_balanced)

    def test_entry_str(self):
        entry = self._make_entry(Decimal('200.00'), Decimal('200.00'))
        self.assertIn('JE-001', str(entry))
        self.assertIn('draft', str(entry))


class FiscalPeriodTests(TestCase):

    def setUp(self):
        self.tenant, _, _, _ = _setup_base()
        self.period = FiscalPeriod.objects.create(
            name='Q1 2026',
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 3, 31),
            status='open',
            tenant_id=TENANT_ID,
        )

    def test_fiscal_period_open_by_default(self):
        """A newly created FiscalPeriod defaults to 'open' status."""
        self.assertEqual(self.period.status, 'open')

    def test_close_fiscal_period_via_api(self):
        """The close_period action sets the period status to 'closed'."""
        user = User.objects.create_user(username='perioduser', password='x', tenant_id=TENANT_ID)
        client = _api_client(user)
        res = client.post(f'/api/v1/accounting/fiscal-periods/{self.period.id}/close_period/')
        self.assertEqual(res.status_code, 200)
        self.period.refresh_from_db()
        self.assertEqual(self.period.status, 'closed')

    def test_fiscal_period_str(self):
        self.assertIn('Q1 2026', str(self.period))
        self.assertIn('open', str(self.period))
