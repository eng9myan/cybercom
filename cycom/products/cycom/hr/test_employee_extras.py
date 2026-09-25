"""EmployeeDocument / EmployeeInsurance API tests -- wired up to fix
app/hr/documents/page.tsx and app/hr/insurance/page.tsx, which called
legacy-RPC model names (hr.document, hr.employee.insurance) with no
backend behind them at all."""

import uuid
from datetime import date

import pytest
from rest_framework.test import APIClient

from products.cycom.hr.models import Employee

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "hr@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["tenant_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def employee(tenant_id):
    return Employee.objects.create(
        tenant_id=tenant_id, employee_number="EMP-DOC-1", first_name="Sam", last_name="Taha",
        hire_date=date(2024, 1, 1),
    )


def test_create_employee_document(admin_client, tenant_id, employee):
    resp = admin_client.post(
        "/api/v1/hr/documents/",
        {"employee": str(employee.id), "document_type": "iqama", "number": "IQ-123", "expiry_date": "2027-01-01"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["employee_name"] == "Sam Taha"


def test_list_employee_documents(admin_client, tenant_id, employee):
    admin_client.post(
        "/api/v1/hr/documents/",
        {"employee": str(employee.id), "document_type": "passport", "expiry_date": "2028-06-01"},
        format="json",
    )
    resp = admin_client.get("/api/v1/hr/documents/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert len(rows) == 1
    assert rows[0]["document_type"] == "passport"


def test_create_employee_insurance(admin_client, tenant_id, employee):
    resp = admin_client.post(
        "/api/v1/hr/insurance/",
        {
            "employee": str(employee.id), "plan_name": "Grade A", "provider": "MedNet",
            "policy_number": "POL-1", "start_date": "2026-01-01", "end_date": "2026-12-31",
        },
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["employee_name"] == "Sam Taha"
    assert resp.data["status"] == "active"


def test_documents_require_auth(tenant_id):
    resp = APIClient().get("/api/v1/hr/documents/")
    assert resp.status_code == 401


def test_insurance_requires_auth(tenant_id):
    resp = APIClient().get("/api/v1/hr/insurance/")
    assert resp.status_code == 401


def test_documents_tenant_isolated(admin_client, tenant_id, employee):
    other_tenant = uuid.uuid4()
    other_employee = Employee.objects.create(
        tenant_id=other_tenant, employee_number="EMP-OTHER", first_name="X", last_name="Y",
        hire_date=date(2024, 1, 1),
    )
    from products.cycom.hr.models import EmployeeDocument

    EmployeeDocument.objects.create(tenant_id=other_tenant, employee=other_employee, document_type="passport")
    resp = admin_client.get("/api/v1/hr/documents/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert rows == []
