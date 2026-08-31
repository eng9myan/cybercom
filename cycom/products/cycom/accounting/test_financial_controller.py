"""
Financial-controller audit (automated): post a realistic set of transactions,
then pull every statement and assert they balance and tie out.

  Trial balance:  total debits == total credits
  P&L:            net_profit == income - expenses
  Balance sheet:  assets == liabilities + equity + current-period earnings
  VAT return:     output - input == net payable
  Payroll:        social security 7.5% / income tax by bracket, net correct
"""

import uuid
from decimal import Decimal

from django.test import TestCase

from products.cycom.accounting.models import Account
from products.cycom.accounting.reports import (
    balance_sheet,
    profit_and_loss,
    trial_balance,
    vat_return,
)
from products.cycom.accounting.services import post_journal_entry
from products.cycom.payroll.rules import annual_income_tax, monthly_income_tax, social_security

T = uuid.uuid4()


def acc(code, name, atype):
    return Account.objects.create(tenant_id=T, code=code, name=name, account_type=atype)


class FinancialControllerAudit(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.bank = acc("1120", "Bank", "asset")
        cls.ar = acc("1130", "Accounts Receivable", "asset")
        cls.out_tax = acc("2120", "Output GST", "liability")
        cls.capital = acc("3100", "Share Capital", "equity")
        cls.revenue = acc("4100", "Revenue", "income")
        cls.cogs = acc("5100", "COGS", "expense")

        # 1) Owner injects 10,000 capital.
        post_journal_entry(tenant_id=T, date="2026-07-01", reference="CAP-1", lines=[
            {"account": cls.bank, "debit": Decimal("10000"), "credit": 0},
            {"account": cls.capital, "debit": 0, "credit": Decimal("10000")},
        ])
        # 2) Sale of 1,000 + 16% GST on credit.
        post_journal_entry(tenant_id=T, date="2026-07-05", reference="INV-1", lines=[
            {"account": cls.ar, "debit": Decimal("1160"), "credit": 0},
            {"account": cls.revenue, "debit": 0, "credit": Decimal("1000")},
            {"account": cls.out_tax, "debit": 0, "credit": Decimal("160")},
        ])
        # 3) Cost of goods, paid from bank.
        post_journal_entry(tenant_id=T, date="2026-07-06", reference="COGS-1", lines=[
            {"account": cls.cogs, "debit": Decimal("600"), "credit": 0},
            {"account": cls.bank, "debit": 0, "credit": Decimal("600")},
        ])

    def test_trial_balance_balances(self):
        tb = trial_balance(T)
        self.assertTrue(tb["balanced"], tb)
        self.assertEqual(tb["total_debit"], Decimal("11160.00"))
        self.assertEqual(tb["total_credit"], Decimal("11160.00"))

    def test_profit_and_loss(self):
        pl = profit_and_loss(T)
        self.assertEqual(pl["total_income"], Decimal("1000.00"))
        self.assertEqual(pl["total_expenses"], Decimal("600.00"))
        self.assertEqual(pl["net_profit"], Decimal("400.00"))

    def test_balance_sheet_ties(self):
        bs = balance_sheet(T)
        # assets: bank 9,400 + AR 1,160 = 10,560
        self.assertEqual(bs["total_assets"], Decimal("10560.00"))
        self.assertEqual(bs["total_liabilities"], Decimal("160.00"))
        self.assertEqual(bs["total_equity"], Decimal("10000.00"))
        self.assertEqual(bs["current_period_earnings"], Decimal("400.00"))
        self.assertTrue(bs["balanced"], bs)

    def test_vat_return(self):
        v = vat_return(T)
        self.assertEqual(v["output_tax"], Decimal("160.00"))
        self.assertEqual(v["input_tax"], Decimal("0.00"))
        self.assertEqual(v["net_payable"], Decimal("160.00"))

    def test_accounting_equation_holds(self):
        bs = balance_sheet(T)
        assets = bs["total_assets"]
        liab_plus_equity = bs["total_liabilities_and_equity"]
        self.assertEqual(assets, liab_plus_equity)


class PayrollStatutoryTests(TestCase):
    def test_social_security_rates(self):
        emp, empr = social_security(Decimal("700"))
        self.assertEqual(emp, Decimal("52.50"))   # 7.5%
        self.assertEqual(empr, Decimal("99.75"))  # 14.25%

    def test_exemption_single_below_threshold(self):
        # basic 700/mo -> 8,400/yr, below the 9,000 single exemption -> no tax
        self.assertEqual(annual_income_tax(Decimal("8400"), "single", False), Decimal("0.00"))

    def test_single_bands(self):
        # 24,000/yr, single, exemption 9,000 -> taxable 15,000:
        # 5,000@5 + 5,000@10 + 5,000@15 = 250 + 500 + 750 = 1,500
        self.assertEqual(annual_income_tax(Decimal("24000"), "single", False), Decimal("1500.00"))

    def test_married_sole_earner_exemption(self):
        # 24,000/yr, married, spouse NOT employed -> exemption 18,000 -> taxable 6,000:
        # 5,000@5 + 1,000@10 = 250 + 100 = 350
        self.assertEqual(annual_income_tax(Decimal("24000"), "married", False), Decimal("350.00"))

    def test_married_spouse_employed_uses_default_exemption(self):
        # spouse employed -> falls back to 9,000 exemption, same as single
        self.assertEqual(annual_income_tax(Decimal("24000"), "married", True), Decimal("1500.00"))

    def test_top_rate_remainder(self):
        # 40,000/yr single, exemption 9,000 -> taxable 31,000:
        # 20,000 across the four bands (250+500+750+1000=2,500) + 11,000@25% = 2,750
        self.assertEqual(annual_income_tax(Decimal("40000"), "single", False), Decimal("5250.00"))

    def test_monthly_income_tax_full_and_prorated(self):
        # basic 2,000/mo, single -> annual 24,000 -> 1,500 tax -> 125/mo
        self.assertEqual(monthly_income_tax(Decimal("2000"), "single", False), Decimal("125.00"))
        # partial month: only 1,000 basic actually earned -> half the tax
        self.assertEqual(
            monthly_income_tax(Decimal("2000"), "single", False, current_basic=Decimal("1000")),
            Decimal("62.50"),
        )


class MultiCurrencyReports(TestCase):
    """Reports state amounts in the base currency: a line's amount is converted
    via exchange_rate before aggregation, so a USD entry doesn't get summed
    at face value alongside base-currency entries."""

    def setUp(self):
        from products.cycom.accounting.models import JournalEntry, JournalLine

        self.T2 = uuid.uuid4()
        self.bank = Account.objects.create(tenant_id=self.T2, code="1120", name="Bank", account_type="asset")
        self.capital = Account.objects.create(tenant_id=self.T2, code="3100", name="Capital", account_type="equity")

        def posted(ref, currency, rate, amount):
            e = JournalEntry.objects.create(
                tenant_id=self.T2, date="2026-07-01", reference=ref,
                currency=currency, status="posted",
            )
            JournalLine.objects.create(tenant_id=self.T2, entry=e, account=self.bank,
                                       debit=Decimal(amount), credit=0, currency=currency, exchange_rate=Decimal(rate))
            JournalLine.objects.create(tenant_id=self.T2, entry=e, account=self.capital,
                                       debit=0, credit=Decimal(amount), currency=currency, exchange_rate=Decimal(rate))

        posted("JOD-1", "JOD", "1.000000", "1000")   # 1000 base
        posted("USD-1", "USD", "0.710000", "100")     # 100 USD -> 71 base

    def test_trial_balance_is_in_base_currency(self):
        tb = trial_balance(self.T2)
        # 1000 (JOD) + 71 (100 USD * 0.71) = 1071, NOT 1100.
        self.assertEqual(tb["total_debit"], Decimal("1071.00"))
        self.assertEqual(tb["total_credit"], Decimal("1071.00"))
        self.assertTrue(tb["balanced"])

    def test_balance_sheet_converts(self):
        bs = balance_sheet(self.T2)
        self.assertEqual(bs["total_assets"], Decimal("1071.00"))
        self.assertTrue(bs["balanced"])
