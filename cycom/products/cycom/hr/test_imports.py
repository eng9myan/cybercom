"""Employee bulk-import engine tests (SQLite via core.settings_test)."""

import uuid

from django.test import TestCase

from products.cycom.hr.imports import run_import, validate_rows
from products.cycom.hr.models import Employee

TENANT = uuid.uuid4()


class BulkImportTests(TestCase):
    def _rows(self):
        return [
            {"employee_no": "EMP-1", "name": "Ahmad Mansour", "email": "ahmad@cycom.jo", "department": "Eng", "role": "Engineer"},
            {"employee_no": "EMP-2", "name": "Rania Shawabkeh", "email": "rania@cycom.jo"},
        ]

    def test_dry_run_writes_nothing(self):
        res = run_import(self._rows(), TENANT, dry_run=True)
        self.assertTrue(res["dry_run"])
        self.assertEqual(res["valid_count"], 2)
        self.assertEqual(res["imported_count"], 0)
        self.assertEqual(Employee.objects.filter(tenant_id=TENANT).count(), 0)

    def test_commit_creates_employees(self):
        res = run_import(self._rows(), TENANT, dry_run=False)
        self.assertEqual(res["imported_count"], 2)
        emp = Employee.objects.get(tenant_id=TENANT, employee_number="EMP-1")
        self.assertEqual(emp.first_name, "Ahmad")
        self.assertEqual(emp.last_name, "Mansour")
        self.assertEqual(emp.job_title, "Engineer")

    def test_missing_required_flagged(self):
        rows = [{"employee_no": "", "name": ""}, {"employee_no": "EMP-9", "name": "Valid Person"}]
        res = run_import(rows, TENANT, dry_run=True)
        self.assertEqual(res["invalid_count"], 1)
        self.assertEqual(res["valid_count"], 1)

    def test_bad_email_flagged(self):
        rows = [{"employee_no": "EMP-3", "name": "Bad Email", "email": "not-an-email"}]
        res = validate_rows(rows, TENANT)
        self.assertFalse(res[0]["valid"])
        self.assertTrue(any("email" in e.lower() for e in res[0]["errors"]))

    def test_duplicate_in_file(self):
        rows = [{"employee_no": "EMP-5", "name": "A"}, {"employee_no": "EMP-5", "name": "B"}]
        res = run_import(rows, TENANT, dry_run=True)
        self.assertEqual(res["invalid_count"], 1)  # second one flagged

    def test_duplicate_against_db_and_partial_accept(self):
        Employee.objects.create(
            tenant_id=TENANT, employee_number="EMP-7", first_name="Existing",
            last_name="One", hire_date="2026-01-01",
        )
        rows = [{"employee_no": "EMP-7", "name": "Clash"}, {"employee_no": "EMP-8", "name": "New Guy"}]
        res = run_import(rows, TENANT, dry_run=False)
        self.assertEqual(res["imported_count"], 1)  # only EMP-8
        self.assertTrue(Employee.objects.filter(tenant_id=TENANT, employee_number="EMP-8").exists())
