"""
SIF AU v3.x provider layer.

The two things worth testing hardest are the RefId promise — minted once,
stable forever, never reused — and the honesty of the coverage report, since
the most damaging outcome here is someone believing CyEd is SIF certified.
"""

import uuid
from datetime import date
from xml.etree import ElementTree as ET

import pytest
from rest_framework.test import APIClient

from products.cyed.attendance.models import AttendanceMark, RollCall
from products.cyed.hr.models import Staff
from products.cyed.org.models import Campus
from products.cyed.sif import mappers
from products.cyed.sif.encoding import to_json, to_xml
from products.cyed.sif.models import SifRefId
from products.cyed.sif.refids import synthetic_local_id
from products.cyed.sis.models import ClassSection, Student

SIF_NS = "{http://www.sifassociation.org/au/datamodel/3.4}"


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="registrar@cyed.edu.au"):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def staff_client(client_for):
    return client_for(["tenant_admin"])


@pytest.fixture
def campus(tenant_id):
    return Campus.objects.create(tenant_id=tenant_id, name="Northside", code="NTH")


@pytest.fixture
def student(tenant_id, campus):
    return Student.objects.create(
        tenant_id=tenant_id, campus=campus, first_name="Mia", last_name="Tran",
        year_level=8, enrolment_status="enrolled", student_number="S1001",
        date_of_birth=date(2012, 4, 3), usi="ABC1234567",
        state_student_number="VSN99", indigenous_status="4",
        language_at_home="Vietnamese", email="mia@student.cyed.edu.au",
    )


# ── the RefId promise ────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_refid_is_minted_once_and_never_changes(tenant_id, student):
    first = mappers.student_personal(student)["@RefId"]
    second = mappers.student_personal(student)["@RefId"]
    assert first == second
    assert SifRefId.objects.filter(
        tenant_id=tenant_id, object_type="StudentPersonal"
    ).count() == 1


@pytest.mark.django_db
def test_a_refid_survives_the_record_changing(tenant_id, student):
    """
    A RefId that moved when a student was renamed would look to a consumer
    like a delete and a create, orphaning everything keyed off the old one.
    """
    before = mappers.student_personal(student)["@RefId"]
    student.last_name = "Nguyen"
    student.year_level = 9
    student.save(update_fields=["last_name", "year_level"])
    assert mappers.student_personal(student)["@RefId"] == before


@pytest.mark.django_db
def test_derived_objects_get_a_stable_synthetic_id(tenant_id, student):
    """
    StudentAttendance is not a table — it is a student, a date and a school.
    Hashing them must give the same id on every run or the registry mints a
    second RefId for the same fact.
    """
    a = synthetic_local_id("StudentAttendance", student.id, date(2026, 8, 11))
    b = synthetic_local_id("StudentAttendance", student.id, date(2026, 8, 11))
    c = synthetic_local_id("StudentAttendance", student.id, date(2026, 8, 12))
    assert a == b
    assert a != c


@pytest.mark.django_db
def test_two_objects_never_share_a_refid(tenant_id, student, campus):
    """One RefId identifies exactly one object; sharing would collide records."""
    refids = {
        mappers.student_personal(student)["@RefId"],
        mappers.student_school_enrollment(student)["@RefId"],
        mappers.school_info(campus)["@RefId"],
    }
    assert len(refids) == 3


@pytest.mark.django_db
def test_refids_are_read_only_over_the_api(staff_client, tenant_id, student):
    mappers.student_personal(student)
    row = SifRefId.objects.get(tenant_id=tenant_id, object_type="StudentPersonal")

    assert staff_client.patch(
        f"/api/v1/sif/refids/{row.id}/", {"refid": str(uuid.uuid4())}, format="json"
    ).status_code == 405
    assert staff_client.delete(f"/api/v1/sif/refids/{row.id}/").status_code == 405


# ── mapping ──────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_student_personal_carries_the_identifiers_a_consumer_needs(tenant_id, student):
    obj = to_json(mappers.student_personal(student))
    assert obj["LocalId"] == "S1001"
    assert obj["StateProvinceId"] == "VSN99"
    assert obj["PersonInfo"]["Name"]["FamilyName"] == "Tran"
    assert obj["PersonInfo"]["Demographics"]["BirthDate"] == "2012-04-03"
    assert obj["MostRecent"]["YearLevel"]["Code"] == "8"
    assert obj["MostRecent"]["SchoolLocalId"] == "NTH"
    assert obj["EnrollmentStatus"] == "A"


@pytest.mark.django_db
def test_foundation_year_is_emitted_as_f(tenant_id, campus):
    """SIF AU writes Foundation as 'F'; CyEd stores it as 0."""
    prep = Student.objects.create(
        tenant_id=tenant_id, campus=campus, first_name="Tiny", last_name="One",
        year_level=0, enrolment_status="enrolled",
    )
    assert mappers.student_personal(prep)["MostRecent"]["YearLevel"]["Code"] == "F"


@pytest.mark.django_db
def test_enrollment_points_back_at_the_student_object(tenant_id, student):
    enrollment = mappers.student_school_enrollment(student)
    assert enrollment["StudentPersonalRefId"] == mappers.student_personal(student)["@RefId"]
    assert enrollment["TimeFrame"] == "Current"


@pytest.mark.django_db
def test_attendance_maps_to_a_daily_value(tenant_id, student):
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)
    roll = RollCall.objects.create(
        tenant_id=tenant_id, class_section=section, date=date(2026, 8, 11)
    )
    mark = AttendanceMark.objects.create(
        tenant_id=tenant_id, roll_call=roll, student=student, status="absent"
    )
    obj = to_json(mappers.student_attendance(mark))
    assert obj["Date"] == "2026-08-11"
    assert obj["DailyAttendanceValue"] == "000"
    assert obj["AttendanceCode"]["Code"] == "absent"


# ── encoding ─────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_absent_values_are_omitted_not_emitted_empty(tenant_id, campus):
    """
    SIF distinguishes absent from empty. `<ACARAId/>` asserts the school has a
    blank ACARA id rather than none on record.
    """
    obj = mappers.school_info(campus)
    assert obj["ACARAId"] is None

    rendered = to_xml("SchoolInfo", obj)
    assert "ACARAId" not in rendered
    assert to_json(obj).get("ACARAId") is None


@pytest.mark.django_db
def test_a_container_left_empty_by_pruning_disappears(tenant_id, campus):
    """A student with no email must not emit an empty EmailList."""
    quiet = Student.objects.create(
        tenant_id=tenant_id, campus=campus, first_name="No", last_name="Email",
        year_level=7, enrolment_status="enrolled",
    )
    assert "EmailList" not in to_json(mappers.student_personal(quiet))["PersonInfo"]


@pytest.mark.django_db
def test_xml_is_namespaced_and_refid_is_an_attribute(tenant_id, student):
    xml = to_xml("StudentPersonal", mappers.student_personal(student))
    root = ET.fromstring(xml)
    assert root.tag == f"{SIF_NS}StudentPersonal"
    assert root.get("RefId")
    assert root.find(f"{SIF_NS}LocalId").text == "S1001"


# ── endpoints ────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_collection_is_served_as_xml_by_default(staff_client, tenant_id, student):
    resp = staff_client.get("/api/v1/sif/objects/StudentPersonal/")
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/xml"
    assert resp["X-CyEd-SIF-Conformance"] == "uncertified-provider"

    root = ET.fromstring(resp.content.decode())
    assert root.tag == f"{SIF_NS}StudentPersonals"
    assert len(root.findall(f"{SIF_NS}StudentPersonal")) == 1


@pytest.mark.django_db
def test_the_json_binding_carries_the_gap_list(staff_client, tenant_id, student):
    """A consumer reading only this payload still learns what is missing."""
    resp = staff_client.get("/api/v1/sif/objects/StudentPersonal/?format=json")
    assert resp.status_code == 200
    assert resp.data["total"] == 1
    assert len(resp.data["StudentPersonals"]) == 1
    assert any("ACARAId" not in g["element"] for g in resp.data["cyed:gaps"])
    assert resp.data["cyed:gaps"]


@pytest.mark.django_db
def test_an_unknown_object_is_refused_with_the_supported_list(staff_client):
    resp = staff_client.get("/api/v1/sif/objects/TeachingGroup/")
    assert resp.status_code == 404
    assert "StudentPersonal" in resp.data["supported"]


@pytest.mark.django_db
def test_a_refid_resolves_back_to_its_object(staff_client, tenant_id, student):
    """The question a consumer asks when reconciling: what is this identifier?"""
    refid = mappers.student_personal(student)["@RefId"]
    resp = staff_client.get(f"/api/v1/sif/refid/{refid}/")
    assert resp.status_code == 200
    assert resp.data["object"] == "StudentPersonal"
    assert resp.data["StudentPersonal"]["LocalId"] == "S1001"


@pytest.mark.django_db
def test_a_derived_refid_resolves_without_a_scan(staff_client, tenant_id, student):
    refid = mappers.student_school_enrollment(student)["@RefId"]
    resp = staff_client.get(f"/api/v1/sif/refid/{refid}/")
    assert resp.status_code == 200
    assert resp.data["object"] == "StudentSchoolEnrollment"


@pytest.mark.django_db
def test_a_retired_refid_reports_gone_not_missing(staff_client, tenant_id, student):
    """
    410 rather than 404: a consumer reads "not found" as "never existed", and
    the RefId did exist — it is retired and will never be reassigned.
    """
    refid = mappers.student_personal(student)["@RefId"]
    student.delete()
    resp = staff_client.get(f"/api/v1/sif/refid/{refid}/")
    assert resp.status_code == 410
    assert "never be reassigned" in resp.data["detail"]


@pytest.mark.django_db
def test_an_unknown_refid_is_a_plain_404(staff_client):
    assert staff_client.get(f"/api/v1/sif/refid/{uuid.uuid4()}/").status_code == 404


@pytest.mark.django_db
def test_a_malformed_refid_does_not_error(staff_client):
    assert staff_client.get("/api/v1/sif/refid/not-a-uuid/").status_code == 404


@pytest.mark.django_db
def test_bulk_student_data_is_staff_only(client_for, tenant_id, student):
    parent = client_for(["parent"], "p@example.com")
    assert parent.get("/api/v1/sif/objects/StudentPersonal/").status_code == 403


# ── the coverage report ──────────────────────────────────────────────────────
@pytest.mark.django_db
def test_coverage_states_plainly_that_this_is_not_certified(staff_client):
    """This report, not a badge, is what an auditor should be given."""
    resp = staff_client.get("/api/v1/sif/coverage/")
    assert resp.status_code == 200
    assert resp.data["conformance"] == "uncertified-provider"
    assert "NOT a certified SIF Zone integration" in resp.data["disclaimer"]

    missing = " ".join(resp.data["not_implemented"])
    assert "Zone registration" in missing
    assert "Event publication" in missing
    assert "certification" in missing


@pytest.mark.django_db
def test_coverage_lists_element_gaps_per_object(staff_client):
    resp = staff_client.get("/api/v1/sif/coverage/")
    gaps = resp.data["element_gaps"]
    assert set(gaps) == set(mappers.OBJECTS)
    # The ACARA id gap is the one that blocks My School matching — it must be
    # stated, not quietly omitted.
    assert any("ACARAId" in g["element"] for g in gaps["SchoolInfo"])
    assert all(g["reason"] for object_gaps in gaps.values() for g in object_gaps)


# ── statutory collections (NAPLAN / NCCD / STATS) ───────────────────────────
# Previously these left the codebase as bespoke CSV/JSON with no SIF envelope
# at all (products.cyed.compliance.services). This section proves they're now
# reachable through the same RefId-stable, gap-honest object pipeline as
# StudentPersonal etc. — not that they match an external certified schema
# (no such schema was available to verify against; see each mapper's GAPS).

@pytest.mark.django_db
def test_naplan_participation_only_covers_eligible_years(tenant_id, campus):
    eligible = Student.objects.create(
        tenant_id=tenant_id, campus=campus, first_name="A", last_name="B",
        year_level=7, enrolment_status="enrolled", usi="X1", indigenous_status="4",
    )
    ineligible = Student.objects.create(
        tenant_id=tenant_id, campus=campus, first_name="C", last_name="D",
        year_level=8, enrolment_status="enrolled",
    )
    obj = mappers.naplan_participation(eligible)
    assert obj["Eligible"] is True
    assert obj["ParticipationStatus"]["Code"] == "P"

    not_eligible_obj = mappers.naplan_participation(ineligible)
    assert not_eligible_obj["Eligible"] is False


@pytest.mark.django_db
def test_naplan_endpoint_scopes_to_eligible_cohort(staff_client, tenant_id, campus):
    Student.objects.create(
        tenant_id=tenant_id, campus=campus, first_name="A", last_name="B",
        year_level=3, enrolment_status="enrolled",
    )
    Student.objects.create(
        tenant_id=tenant_id, campus=campus, first_name="C", last_name="D",
        year_level=1, enrolment_status="enrolled",  # not a NAPLAN year
    )
    resp = staff_client.get("/api/v1/sif/objects/NAPLANParticipation/?format=json")
    assert resp.status_code == 200
    assert resp.data["total"] == 1


@pytest.mark.django_db
def test_nccd_disability_status_is_stable_and_carries_the_record(tenant_id, student):
    from products.cyed.compliance.models import NCCDRecord

    record = NCCDRecord.objects.create(
        tenant_id=tenant_id, student=student, collection_year=2026,
        category="cognitive", level_of_adjustment="supplementary",
    )
    first = mappers.nccd_disability_status(record)
    second = mappers.nccd_disability_status(record)
    assert first["@RefId"] == second["@RefId"]
    assert first["DisabilityCategory"]["Code"] == "cognitive"
    assert first["LevelOfAdjustment"]["Code"] == "supplementary"
    assert first["StudentPersonalRefId"] == mappers.student_personal(student)["@RefId"]


@pytest.mark.django_db
def test_nccd_endpoint_returns_records(staff_client, tenant_id, student):
    from products.cyed.compliance.models import NCCDRecord

    NCCDRecord.objects.create(
        tenant_id=tenant_id, student=student, collection_year=2026,
        category="physical", level_of_adjustment="substantial",
    )
    resp = staff_client.get("/api/v1/sif/objects/NCCDDisabilityStatus/?format=json")
    assert resp.status_code == 200
    assert resp.data["total"] == 1
    assert resp.data["NCCDDisabilityStatuses"][0]["DisabilityCategory"]["Code"] == "physical"


@pytest.mark.django_db
def test_statistical_return_excludes_unenrolled_students(staff_client, tenant_id, campus):
    Student.objects.create(
        tenant_id=tenant_id, campus=campus, first_name="A", last_name="B",
        year_level=5, enrolment_status="enrolled",
    )
    Student.objects.create(
        tenant_id=tenant_id, campus=campus, first_name="C", last_name="D",
        year_level=6, enrolment_status="withdrawn",
    )
    resp = staff_client.get("/api/v1/sif/objects/StudentStatisticalReturn/?format=json")
    assert resp.status_code == 200
    assert resp.data["total"] == 1


@pytest.mark.django_db
def test_new_statutory_objects_round_trip_by_refid(staff_client, tenant_id, student):
    from products.cyed.compliance.models import NCCDRecord

    NCCDRecord.objects.create(
        tenant_id=tenant_id, student=student, collection_year=2026,
        category="sensory", level_of_adjustment="extensive",
    )
    listing = staff_client.get("/api/v1/sif/objects/NCCDDisabilityStatus/?format=json")
    refid = listing.data["NCCDDisabilityStatuses"][0]["@RefId"]
    resolved = staff_client.get(f"/api/v1/sif/refid/{refid}/")
    assert resolved.status_code == 200
    assert resolved.data["object"] == "NCCDDisabilityStatus"
