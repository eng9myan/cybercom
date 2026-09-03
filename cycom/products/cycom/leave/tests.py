"""Leave management tests (SQLite via settings_test)."""

import uuid
from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from products.cycom.hr.models import Employee
from products.cycom.leave.models import LeaveRequest, LeaveType
from products.cycom.leave.services import leave_balance, validate_approvable

T = uuid.uuid4()


class LeaveTests(TestCase):
    def setUp(self):
        self.emp = Employee.objects.create(
            tenant_id=T, employee_number="E1", first_name="Omar", last_name="H", hire_date="2025-01-01"
        )
        self.annual = LeaveType.objects.create(
            tenant_id=T, name="Annual", code="ANN", is_paid=True, days_per_year=Decimal("14")
        )

    def _req(self, start, end, status="submitted"):
        r = LeaveRequest.objects.create(
            tenant_id=T, employee=self.emp, leave_type=self.annual,
            start_date=start, end_date=end, status=status,
        )
        r.days = r.compute_days()
        r.save(update_fields=["days"])
        return r

    def test_days_inclusive(self):
        r = self._req(date(2026, 3, 1), date(2026, 3, 5))
        self.assertEqual(r.days, 5)  # inclusive

    def test_balance_reflects_approved_only(self):
        self._req(date(2026, 3, 1), date(2026, 3, 5), status="approved")  # 5 taken
        self._req(date(2026, 4, 1), date(2026, 4, 2), status="submitted")  # not counted
        bal = leave_balance(T, self.emp.id, self.annual, year=2026)
        self.assertEqual(bal["allocated"], Decimal("14"))
        self.assertEqual(bal["taken"], Decimal("5"))
        self.assertEqual(bal["remaining"], Decimal("9"))

    def test_overlap_blocked(self):
        self._req(date(2026, 3, 1), date(2026, 3, 10), status="approved")
        clash = self._req(date(2026, 3, 5), date(2026, 3, 7))
        with self.assertRaises(ValidationError):
            validate_approvable(clash)

    def test_over_allocation_blocked(self):
        self._req(date(2026, 1, 1), date(2026, 1, 10), status="approved")   # 10 taken
        big = self._req(date(2026, 6, 1), date(2026, 6, 8))                  # wants 8, only 4 left
        with self.assertRaises(ValidationError):
            validate_approvable(big)

    def test_within_balance_ok(self):
        ok = self._req(date(2026, 2, 1), date(2026, 2, 3))  # 3 days, 14 available
        validate_approvable(ok)  # should not raise
