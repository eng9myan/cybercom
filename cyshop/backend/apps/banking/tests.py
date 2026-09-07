from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.tenants.models import Company, Tenant
from .models import BankAccount, BankStatementLine, ReconciliationSession
from . import services


class BankingTests(TestCase):
    def setUp(self):
        self.t = Tenant.objects.create(name="T", subdomain="t-bank")
        self.co = Company.objects.create(tenant_id=self.t.id, name="Acme")
        self.ba = BankAccount.objects.create(
            tenant_id=self.t.id, company=self.co, name="Ops", currency="SAR",
            opening_balance=0)

    def test_csv_import_amount_column(self):
        csv = ("date,description,reference,amount\n"
               "2026-09-01,Card settlement,POS,1240.50\n"
               "2026-09-02,Supplier payment,PO-9,-430.00\n")
        stmt, lines = services.import_statement_csv(self.ba, csv, tenant_id=self.t.id)
        self.assertEqual(len(lines), 2)
        self.assertEqual(stmt.closing_balance, Decimal("810.50"))
        self.assertEqual(lines[1].amount, Decimal("-430.00"))

    def test_csv_import_debit_credit_columns(self):
        csv = ("Date,Description,Debit,Credit\n"
               "01/09/2026,Deposit,,500\n"
               "02/09/2026,Fee,12,\n")
        _, lines = services.import_statement_csv(self.ba, csv, tenant_id=self.t.id)
        self.assertEqual(lines[0].amount, Decimal("500.00"))
        self.assertEqual(lines[1].amount, Decimal("-12.00"))

    def test_manual_match_moves_book_balance(self):
        csv = "date,description,amount\n2026-09-01,X,100\n"
        _, lines = services.import_statement_csv(self.ba, csv, tenant_id=self.t.id)
        ln = lines[0]
        self.assertEqual(self.ba.book_balance, Decimal("0.00"))
        ln.matched = ln.reconciled = True
        ln.save()
        self.assertEqual(self.ba.book_balance, Decimal("100.00"))

    def test_session_difference(self):
        csv = "date,description,amount\n2026-09-01,X,100\n"
        _, lines = services.import_statement_csv(self.ba, csv, tenant_id=self.t.id)
        lines[0].matched = lines[0].reconciled = True
        lines[0].save()
        s = ReconciliationSession.objects.create(
            tenant_id=self.t.id, bank_account=self.ba,
            period_start=date(2026, 9, 1), period_end=date(2026, 9, 30),
            statement_closing_balance=Decimal("100.00"))
        services.complete(s)
        s.refresh_from_db()
        self.assertEqual(s.difference, Decimal("0.00"))
        self.assertEqual(s.status, "completed")
