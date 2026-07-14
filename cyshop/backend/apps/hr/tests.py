import uuid
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from apps.tenants.models import Tenant, Company, Department, Branch
from .models import Employee, Contract, LeaveType, LeaveRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_tenant(suffix=None):
    suffix = suffix or uuid.uuid4().hex[:6]
    return Tenant.objects.create(name='Test Corp', subdomain=f'test-{suffix}')


def make_company(tenant):
    return Company.objects.create(name='Test Company', tenant_id=tenant.id)


def make_department(company, tenant, name='Engineering'):
    return Department.objects.create(company=company, name=name, tenant_id=tenant.id)


def make_branch(company, tenant):
    return Branch.objects.create(
        company=company, name='Main Branch', address='123 Main St', tenant_id=tenant.id
    )


def make_employee(tenant, **kwargs):
    defaults = dict(
        employee_id=f'EMP{uuid.uuid4().hex[:4].upper()}',
        first_name='John',
        last_name='Doe',
        employment_type='full_time',
        hire_date='2024-01-01',
    )
    defaults.update(kwargs)
    return Employee.objects.create(tenant=tenant, **defaults)


def make_leave_type(tenant, name='Annual Leave'):
    return LeaveType.objects.create(tenant=tenant, name=name, days_per_year=21)


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class EmployeeModelTests(TestCase):

    def setUp(self):
        self.tenant = make_tenant()
        self.company = make_company(self.tenant)

    def test_create_employee(self):
        """Creating an Employee sets defaults and links to the correct tenant."""
        emp = make_employee(self.tenant)
        self.assertIsNotNone(emp.id)
        self.assertEqual(emp.tenant, self.tenant)
        self.assertEqual(emp.status, 'active')
        self.assertEqual(emp.currency, 'SAR')

    def test_filter_by_tenant(self):
        """Employees from different tenants are isolated by tenant_id."""
        tenant2 = make_tenant()
        make_employee(self.tenant)
        make_employee(self.tenant)
        make_employee(tenant2)
        result = Employee.objects.filter(tenant_id=self.tenant.id)
        self.assertEqual(result.count(), 2)

    def test_employee_full_name_property(self):
        """Employee.full_name returns 'first_name last_name'."""
        emp = make_employee(self.tenant, first_name='Alice', last_name='Smith')
        self.assertEqual(emp.full_name, 'Alice Smith')

    def test_list_employees_by_department(self):
        """Filtering by department returns only matching employees."""
        dept_eng = make_department(self.company, self.tenant, name='Engineering')
        dept_sales = make_department(self.company, self.tenant, name='Sales')
        make_employee(self.tenant, department=dept_eng)
        make_employee(self.tenant, department=dept_eng)
        make_employee(self.tenant, department=dept_sales)
        result = Employee.objects.filter(tenant_id=self.tenant.id, department=dept_eng)
        self.assertEqual(result.count(), 2)


class LeaveTests(TestCase):

    def setUp(self):
        self.tenant = make_tenant()
        self.employee = make_employee(self.tenant)
        self.leave_type = make_leave_type(self.tenant)

    def test_create_leave_request(self):
        """A new LeaveRequest defaults to 'pending' status."""
        lr = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date='2024-07-01',
            end_date='2024-07-05',
            days_requested=Decimal('5.0'),
        )
        self.assertIsNotNone(lr.id)
        self.assertEqual(lr.status, 'pending')

    def test_approve_leave(self):
        """A leave request can be transitioned to 'approved' with a timestamp."""
        lr = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date='2024-07-01',
            end_date='2024-07-05',
            days_requested=Decimal('5.0'),
        )
        lr.status = 'approved'
        lr.approved_at = timezone.now()
        lr.save()
        lr.refresh_from_db()
        self.assertEqual(lr.status, 'approved')
        self.assertIsNotNone(lr.approved_at)

    def test_reject_leave(self):
        """A leave request can be transitioned to 'rejected'."""
        lr = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date='2024-07-10',
            end_date='2024-07-12',
            days_requested=Decimal('3.0'),
        )
        lr.status = 'rejected'
        lr.save()
        lr.refresh_from_db()
        self.assertEqual(lr.status, 'rejected')


class ContractTests(TestCase):

    def setUp(self):
        self.tenant = make_tenant()
        self.employee = make_employee(self.tenant)

    def test_create_contract(self):
        """Creating a Contract sets is_active=True and defaults empty JSONFields."""
        contract = Contract.objects.create(
            employee=self.employee,
            contract_type='permanent',
            start_date='2024-01-01',
            gross_salary=Decimal('5000.00'),
        )
        self.assertIsNotNone(contract.id)
        self.assertTrue(contract.is_active)
        self.assertEqual(contract.allowances, {})
        self.assertEqual(contract.deductions, {})
