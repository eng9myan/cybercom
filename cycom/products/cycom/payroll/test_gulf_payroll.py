"""Saudi (GOSI) + UAE (GPSSA / gratuity) statutory payroll tests.

Rates sourced 2026-08 (see rules.py header). KSA/UAE have no personal income tax.
"""

from decimal import Decimal

from django.test import SimpleTestCase

from products.cycom.payroll.rules import (
    gosi,
    statutory_income_tax,
    statutory_social_security,
    uae_gratuity,
)

D = Decimal


class SaudiGosiTests(SimpleTestCase):
    def test_saudi_national_2026_rates_on_basic_plus_housing(self):
        emp, empr = gosi(D("20000"), D("5000"))  # wage 25,000 (< cap)
        self.assertEqual(emp, D("2687.50"))   # 25000 * 10.75%
        self.assertEqual(empr, D("3187.50"))  # 25000 * 12.75%

    def test_wage_cap_applies(self):
        emp, empr = gosi(D("50000"), D("10000"))  # 60,000 -> capped at 45,000
        self.assertEqual(emp, D("4837.50"))   # 45000 * 10.75%
        self.assertEqual(empr, D("5737.50"))  # 45000 * 12.75%

    def test_expat_is_employer_2pct_only(self):
        emp, empr = gosi(D("20000"), D("5000"), saudi=False)
        self.assertEqual(emp, D("0.00"))
        self.assertEqual(empr, D("500.00"))   # 25000 * 2%

    def test_legacy_saudi_rates(self):
        emp, empr = gosi(D("10000"), saudi=True, legacy=True)
        self.assertEqual(emp, D("975.00"))    # 10000 * 9.75%
        self.assertEqual(empr, D("1175.00"))  # 10000 * 11.75%

    def test_no_income_tax(self):
        self.assertEqual(statutory_income_tax("SA", D("240000")), D("0.00"))


class UaeGratuityTests(SimpleTestCase):
    def test_first_five_years_21_days(self):
        # basic 30,000 -> daily 1,000; 3 yrs * 21 days = 63,000
        self.assertEqual(uae_gratuity(D("30000"), D("3")), D("63000.00"))

    def test_after_five_years_30_days(self):
        # 5*21*1000 + 1*30*1000 = 135,000
        self.assertEqual(uae_gratuity(D("30000"), D("6")), D("135000.00"))

    def test_capped_at_24_months(self):
        self.assertEqual(uae_gratuity(D("30000"), D("40")), D("720000.00"))  # 24 * 30000

    def test_uae_national_pension_and_no_tax(self):
        emp, empr = statutory_social_security("AE", D("20000"), national=True)
        self.assertEqual(emp, D("1000.00"))   # 20000 * 5%
        self.assertEqual(empr, D("2500.00"))  # 20000 * 12.5%
        # Expat: no monthly contribution.
        self.assertEqual(statutory_social_security("AE", D("20000")), (D("0.00"), D("0.00")))
        self.assertEqual(statutory_income_tax("AE", D("240000")), D("0.00"))


class DispatcherTests(SimpleTestCase):
    def test_jordan_still_works(self):
        emp, empr = statutory_social_security("JO", D("1000"))
        self.assertEqual(emp, D("75.00"))     # 7.5%
        self.assertEqual(empr, D("142.50"))   # 14.25%

    def test_unknown_country_raises(self):
        with self.assertRaises(ValueError):
            statutory_social_security("QA", D("1000"))
