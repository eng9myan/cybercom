import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.library.models import Book
from products.cyed.sis.models import Student


@pytest.fixture
def admin(mint_token, mock_jwks, tenant_id):
    token = mint_token({"sub": str(uuid.uuid4()), "email": "a@cyed.edu.au", "tenant_id": str(tenant_id),
                        "realm_access": {"roles": ["tenant_admin"]}})
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return c


@pytest.mark.django_db
def test_borrow_and_return_adjusts_copies(admin, tenant_id):
    book = Book.objects.create(tenant_id=tenant_id, title="Storm Boy", copies_total=1, copies_available=1)
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)

    loan = admin.post("/api/v1/library/loans/", {"book": str(book.id), "student": str(student.id)}, format="json")
    assert loan.status_code == 201, loan.data
    book.refresh_from_db()
    assert book.copies_available == 0

    # No copies left → next borrow blocked.
    s2 = Student.objects.create(tenant_id=tenant_id, first_name="Ben", last_name="Ng", year_level=8)
    blocked = admin.post("/api/v1/library/loans/", {"book": str(book.id), "student": str(s2.id)}, format="json")
    assert blocked.status_code == 400

    ret = admin.post(f"/api/v1/library/loans/{loan.data['id']}/return_book/")
    assert ret.status_code == 200
    book.refresh_from_db()
    assert book.copies_available == 1
