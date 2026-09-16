import struct
import uuid
import zlib

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token(
            {"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
             "realm_access": {"roles": roles}}
        )
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


def _tiny_jpeg() -> bytes:
    # Minimal valid-enough JPEG: SOI + a SOF0 marker declaring 1x1 dimensions.
    # (jpeg_info only needs the SOF marker to read width/height/components.)
    return (
        b"\xff\xd8"                        # SOI
        b"\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03"  # SOF0: h=1,w=1,components=3
        b"\x01\x11\x00\x02\x11\x01\x03\x11\x01"
        b"\xff\xd9"                        # EOI
    )


@pytest.mark.django_db
def test_profile_get_and_staff_update(client_for, tenant_id):
    staff = client_for(["tenant_admin"])
    got = staff.get("/api/v1/school/profile/")
    assert got.status_code == 200
    assert "name" in got.data

    upd = staff.patch("/api/v1/school/profile/",
                      {"name": "Riverside Secondary College", "suburb": "Parramatta", "state": "NSW",
                       "principal_name": "Dr. Lee"}, format="json")
    assert upd.status_code == 200
    assert upd.data["name"] == "Riverside Secondary College"


@pytest.mark.django_db
def test_profile_update_is_staff_only(client_for, tenant_id):
    parent = client_for(["parent"], email="p@home.com")
    assert parent.get("/api/v1/school/profile/").status_code == 200  # readable
    assert parent.patch("/api/v1/school/profile/", {"name": "Hacked"}, format="json").status_code == 403


@pytest.mark.django_db
def test_logo_upload_and_serve(client_for, tenant_id):
    staff = client_for(["tenant_admin"])
    logo = SimpleUploadedFile("logo.jpg", _tiny_jpeg(), content_type="image/jpeg")
    up = staff.post("/api/v1/school/logo/", {"logo": logo}, format="multipart")
    assert up.status_code == 200
    assert up.data["embeddable"] is True

    served = staff.get("/api/v1/school/logo/")
    assert served.status_code == 200
    assert served["Content-Type"] == "image/jpeg"
    assert served.content[:2] == b"\xff\xd8"


@pytest.mark.django_db
def test_logo_embedded_in_report_pdf(client_for, tenant_id):
    from products.cyed.school.models import get_profile
    from products.cyed.reporting.documents import build_snapshot, content_hash, render_report_pdf
    from products.cyed.reporting.models import ReportCard, ReportCardEntry
    from products.cyed.sis.models import Student

    p = get_profile(tenant_id)
    p.name = "Riverside Secondary College"
    p.logo_bytes = _tiny_jpeg()
    p.logo_content_type = "image/jpeg"
    p.save()

    student = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)
    rc = ReportCard.objects.create(tenant_id=tenant_id, student=student, term="Semester 1")
    ReportCardEntry.objects.create(tenant_id=tenant_id, report_card=rc, subject="Mathematics",
                                   achievement="B", effort="high", comment="Strong progress.")
    snap = build_snapshot(rc)
    pdf = render_report_pdf(snap, content_hash(snap), 1, logo_jpeg=bytes(p.logo_bytes))
    assert pdf[:5] == b"%PDF-"
    # School name is frozen onto the snapshot and the logo XObject is embedded.
    assert snap["school"]["name"] == "Riverside Secondary College"
    assert b"/Image" in pdf and b"DCTDecode" in pdf


@pytest.mark.django_db
def test_report_design_per_school(tenant_id):
    from products.cyed.school.models import get_profile
    from products.cyed.reporting.documents import build_snapshot, content_hash, render_report_pdf
    from products.cyed.reporting.models import ReportCard, ReportCardEntry
    from products.cyed.sis.models import Student

    p = get_profile(tenant_id)
    p.report_title = "Semester Achievement Report"
    p.report_show_effort = False
    p.report_footer = "Nurturing curious minds since 1998."
    p.save()

    student = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)
    rc = ReportCard.objects.create(tenant_id=tenant_id, student=student, term="Semester 1")
    ReportCardEntry.objects.create(tenant_id=tenant_id, report_card=rc, subject="Mathematics",
                                   achievement="B", effort="high", comment="Good.")
    snap = build_snapshot(rc)
    pdf = render_report_pdf(snap, content_hash(snap), 1)

    # Design is frozen into the snapshot and honoured in the PDF.
    assert snap["school"]["design"]["title"] == "Semester Achievement Report"
    assert b"(Semester Achievement Report)" in pdf
    assert b"(Effort)" not in pdf  # effort column hidden by design
    assert b"(Nurturing curious minds since 1998.)" in pdf
