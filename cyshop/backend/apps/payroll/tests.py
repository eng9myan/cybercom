import uuid
from decimal import Decimal
from django.test import TestCase

from apps.tenants.models import Tenant
from apps.hr.models import Employee
from .models import PayrollBatch, Payslip, PayslipLine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_tenant(suffix=None):
    suffix = suffix or uuid.uuid4().hex[:6]
    return Tenant.objects.create(name='Pay Corp', subdomain=f'pay-{suffix}')


def make_employee(tenant):
    return Employee.objects.create(
        tenant=tenant,
        employee_id=f'EMP{uuid.uuid4().hex[:4].upper()}',
        first_name='Test',
        last_name='Employee',
        employment_type='full_time',
        hire_date='2024-01-01',
    )


def make_batch(tenant, name='July 2024 Payroll', **kwargs):
    defaults = dict(period_start='2024-07-01', period_end='2024-07-31')
    defaults.update(kwargs)
    return PayrollBatch.objects.create(tenant=tenant, name=name, **defaults)


def make_payslip(batch, employee, gross=Decimal('5000.00'), **kwargs):
    return Payslip.objects.create(
        batch=batch,
        employee=employee,
        gross_salary=gross,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class PayrollBatchTests(TestCase):

    def setUp(self):
        self.tenant = make_tenant()

    def test_create_batch(self):
        """Creating a PayrollBatch sets status='draft' and zero totals."""
        batch = make_batch(self.tenant)
        self.assertIsNotNone(batch.id)
        self.assertEqual(batch.status, 'draft')
        self.assertEqual(batch.total_gross, 0)
        self.assertEqual(batch.total_net, 0)

    def test_approve_batch(self):
        """A batch can be transitioned to 'approved' status."""
        batch = make_batch(self.tenant)
        batch.status = 'approved'
        batch.save()
        batch.refresh_from_db()
        self.assertEqual(batch.status, 'approved')

    def test_total_update(self):
        """update_totals() correctly aggregates gross and net from payslips."""
        batch = make_batch(self.tenant)
        emp1 = make_employee(self.tenant)
        emp2 = make_employee(self.tenant)
        # emp1: net = 5000 + 0 - 0 = 5000
        make_payslip(batch, emp1, gross=Decimal('5000.00'))
        # emp2: net = 3000 + 500 - 200 = 3300
        make_payslip(
            batch, emp2,
            gross=Decimal('3000.00'),
            allowances_total=Decimal('500.00'),
            deductions_total=Decimal('200.00'),
        )
        batch.update_totals()
        self.assertEqual(batch.total_gross, Decimal('8000.00'))
        self.assertEqual(batch.total_net, Decimal('8300.00'))

    def test_batch_listing(self):
        """Multiple batches for the same tenant are all returned."""
        make_batch(self.tenant, name='July 2024')
        make_batch(self.tenant, name='August 2024',
                   period_start='2024-08-01', period_end='2024-08-31')
        result = PayrollBatch.objects.filter(tenant_id=self.tenant.id)
        self.assertEqual(result.count(), 2)

    def test_tenant_isolation(self):
        """Batches from different tenants do not bleed into each other."""
        tenant2 = make_tenant()
        make_batch(self.tenant)
        make_batch(tenant2)
        result = PayrollBatch.objects.filter(tenant_id=self.tenant.id)
        self.assertEqual(result.count(), 1)


class PayslipTests(TestCase):

    def setUp(self):
        self.tenant = make_tenant()
        self.employee = make_employee(self.tenant)
        self.batch = make_batch(self.tenant)

    def test_create_payslip(self):
        """Creating a Payslip sets status='draft' and records gross_salary."""
        slip = make_payslip(self.batch, self.employee, gross=Decimal('6000.00'))
        self.assertIsNotNone(slip.id)
        self.assertEqual(slip.gross_salary, Decimal('6000.00'))
        self.assertEqual(slip.status, 'draft')

    def test_net_calculation(self):
        """Payslip.save() automatically computes net = gross + allowances - deductions."""
        slip = Payslip.objects.create(
            batch=self.batch,
            employee=self.employee,
            gross_salary=Decimal('5000.00'),
            allowances_total=Decimal('800.00'),
            deductions_total=Decimal('300.00'),
        )
        # 5000 + 800 - 300 = 5500
        self.assertEqual(slip.net_salary, Decimal('5500.00'))

    def test_line_creation(self):
        """PayslipLines can be created and are accessible via the reverse relation."""
        slip = make_payslip(self.batch, self.employee)
        line = PayslipLine.objects.create(
            payslip=slip,
            line_type='earning',
            code='BASIC',
            name='Basic Salary',
            amount=Decimal('5000.00'),
        )
        self.assertIsNotNone(line.id)
        self.assertEqual(slip.lines.count(), 1)
        self.assertEqual(slip.lines.first().code, 'BASIC')
