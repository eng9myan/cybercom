"""Problem list, order sets, eMAR and secure messaging (2026-10-02 gap close)."""
import uuid
from datetime import date, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from platform.common.tenant_context import tenant_context


def _client(mint_token, tenant, roles=("physician",), sub=None, email="dr@x.io"):
    c = APIClient()
    tok = mint_token({"sub": str(sub or uuid.uuid4()), "email": email, "tenant_id": str(tenant),
                      "realm_access": {"roles": list(roles)}, "roles": list(roles)})
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {tok}", HTTP_X_TENANT_ID=str(tenant))
    return c


def _patient(tenant):
    from products.cymed.core.patients.models import Patient

    with tenant_context(tenant):
        return Patient.objects.create(tenant_id=tenant, first_name="Ada", last_name="Test",
                                      dob=date(1970, 1, 1), mrn=f"MRN-{uuid.uuid4().hex[:8]}")


def _rows(resp):
    return resp.data.get("results", resp.data) if isinstance(resp.data, dict) else resp.data


# ── Problem list ─────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_problem_list_shows_active_problems_only(mint_token, mock_jwks):
    from products.cymed.core.clinical.models import Condition

    t = uuid.uuid4()
    p = _patient(t)
    with tenant_context(t):
        def cond(code, **kw):
            return Condition.objects.create(tenant_id=t, patient=p, code=code, display=code,
                                            system="icd11", recorded_by="dr", **kw)
        htn = cond("BA00")
        cond("5A11", clinical_status="resolved")
        cond("CA40", category="encounter_diagnosis")
        cond("XX00", verification_status="refuted")
    c = _client(mint_token, t)
    codes = [r["code"] for r in c.get(f"/api/v1/clinical/conditions/problem-list/?patient={p.id}").data]
    assert codes == ["BA00"]
    assert c.post(f"/api/v1/clinical/conditions/{htn.id}/resolve/", {}, format="json").status_code == 200
    assert c.get(f"/api/v1/clinical/conditions/problem-list/?patient={p.id}").data == []
    history = c.get(f"/api/v1/clinical/conditions/problem-list/?patient={p.id}&include_resolved=1").data
    assert {r["code"] for r in history} == {"BA00", "5A11"}


# ── Order sets ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_order_set_applies_one_order_per_type(mint_token, mock_jwks):
    from products.cymed.core.orders.models import Order

    t = uuid.uuid4()
    p = _patient(t)
    c = _client(mint_token, t)
    created = c.post("/api/v1/order-sets/", {
        "code": "CHEST-PAIN", "name": "Chest pain workup",
        "items": [
            {"order_type": "laboratory", "code": "6598-7", "display": "Troponin T", "priority": "stat"},
            {"order_type": "laboratory", "code": "2345-7", "display": "Glucose"},
            {"order_type": "imaging", "code": "36643-5", "display": "Chest X-ray"},
            {"order_type": "medication", "code": "1191", "display": "Aspirin", "default_selected": False},
        ],
    }, format="json")
    assert created.status_code == 201, created.data
    applied = c.post(f"/api/v1/order-sets/{created.data['id']}/apply/", {"patient": str(p.id)}, format="json")
    assert applied.status_code == 201, applied.data
    by_type = {o["order_type"]: o for o in applied.data}
    assert set(by_type) == {"laboratory", "imaging"}  # unticked aspirin not ordered
    assert by_type["laboratory"]["priority"] == "stat"  # most urgent item wins
    assert len(by_type["laboratory"]["items"]) == 2
    assert Order.objects.filter(patient=p, status="active").count() == 2


@pytest.mark.django_db
def test_order_set_rejects_another_tenants_patient(mint_token, mock_jwks):
    t, other = uuid.uuid4(), uuid.uuid4()
    theirs = _patient(other)
    c = _client(mint_token, t)
    s = c.post("/api/v1/order-sets/", {"code": "X", "name": "X", "items": [
        {"order_type": "laboratory", "code": "1", "display": "Test"}]}, format="json")
    resp = c.post(f"/api/v1/order-sets/{s.data['id']}/apply/", {"patient": str(theirs.id)}, format="json")
    assert resp.status_code == 400


# ── eMAR ─────────────────────────────────────────────────────────────────

def _med_order(tenant, **kw):
    from products.cymed.pharmacy.prescriptions.models import MedicationOrder

    defaults = dict(order_number=f"MO-{uuid.uuid4().hex[:8]}", patient_id=uuid.uuid4(),
                    admission_id=uuid.uuid4(), prescriber_id=uuid.uuid4(), status="verified",
                    drug_code="RX-197361", drug_name="Amlodipine 5mg", dose="5", dose_unit="mg",
                    route="oral", frequency="BID")
    defaults.update(kw)
    return MedicationOrder.objects.create(tenant_id=tenant, **defaults)


@pytest.mark.django_db
def test_mar_schedule_and_five_rights(mint_token, mock_jwks):
    from products.cymed.hospital.nursing.models import MedicationAdministration

    t = uuid.uuid4()
    order = _med_order(t)
    nurse = _client(mint_token, t, roles=("nurse",), email="rn@x.io")
    gen = nurse.post("/api/v1/hospital/nursing/mar/generate/",
                     {"medication_order": str(order.id), "hours": 24}, format="json")
    assert gen.status_code == 201, gen.data
    assert len(gen.data) == 2  # BID
    again = nurse.post("/api/v1/hospital/nursing/mar/generate/",
                       {"medication_order": str(order.id), "hours": 24}, format="json")
    assert again.data == []  # idempotent

    dose = MedicationAdministration.objects.filter(medication_order=order).first()
    # Put the dose inside its window so timing is not what's under test.
    MedicationAdministration.objects.filter(pk=dose.pk).update(scheduled_at=timezone.now())
    url = f"/api/v1/hospital/nursing/mar/{dose.id}/administer/"
    wrong_patient = nurse.post(url, {"patient_barcode": str(uuid.uuid4()),
                                     "medication_barcode": order.drug_code}, format="json")
    assert wrong_patient.status_code == 400 and "Wrong patient" in wrong_patient.data["detail"]
    wrong_drug = nurse.post(url, {"patient_barcode": str(order.patient_id),
                                  "medication_barcode": "RX-OTHER"}, format="json")
    assert "Wrong medication" in wrong_drug.data["detail"]
    ok = nurse.post(url, {"patient_barcode": str(order.patient_id),
                          "medication_barcode": order.drug_code}, format="json")
    assert ok.status_code == 200, ok.data
    assert ok.data["status"] == "given" and ok.data["administered_by"] == "rn@x.io"
    twice = nurse.post(url, {"patient_barcode": str(order.patient_id),
                             "medication_barcode": order.drug_code}, format="json")
    assert twice.status_code == 400


@pytest.mark.django_db
def test_mar_late_dose_needs_reason_and_controlled_needs_witness(mint_token, mock_jwks):
    from products.cymed.hospital.nursing.models import MedicationAdministration

    t = uuid.uuid4()
    order = _med_order(t, drug_code="RX-MORPH", drug_name="Morphine 2mg", dose="2",
                       is_controlled=True, frequency="Q4H")
    nurse = _client(mint_token, t, roles=("nurse",), email="rn@x.io")
    nurse.post("/api/v1/hospital/nursing/mar/generate/", {"medication_order": str(order.id)}, format="json")
    dose = MedicationAdministration.objects.filter(medication_order=order).first()
    MedicationAdministration.objects.filter(pk=dose.pk).update(scheduled_at=timezone.now() - timedelta(hours=3))
    url = f"/api/v1/hospital/nursing/mar/{dose.id}/administer/"
    scan = {"patient_barcode": str(order.patient_id), "medication_barcode": order.drug_code}
    late = nurse.post(url, scan, format="json")
    assert "window" in late.data["detail"]
    no_witness = nurse.post(url, {**scan, "reason": "patient in imaging"}, format="json")
    assert "witness" in no_witness.data["detail"]
    self_witness = nurse.post(url, {**scan, "reason": "patient in imaging", "witness": "rn@x.io"}, format="json")
    assert "different person" in self_witness.data["detail"]
    ok = nurse.post(url, {**scan, "reason": "patient in imaging", "witness": "rn2@x.io"}, format="json")
    assert ok.status_code == 200 and ok.data["witnessed_by"] == "rn2@x.io"


@pytest.mark.django_db
def test_mar_prn_requires_indication_and_unverified_order_is_blocked(mint_token, mock_jwks):
    t = uuid.uuid4()
    prn = _med_order(t, order_type="prn", frequency="PRN", drug_code="RX-APAP")
    nurse = _client(mint_token, t, roles=("nurse",))
    scan = {"medication_order": str(prn.id), "patient_barcode": str(prn.patient_id),
            "medication_barcode": "RX-APAP"}
    assert nurse.post("/api/v1/hospital/nursing/mar/prn/", scan, format="json").status_code == 400
    given = nurse.post("/api/v1/hospital/nursing/mar/prn/", {**scan, "reason": "pain 6/10"}, format="json")
    assert given.status_code == 201 and given.data["status"] == "given"

    pending = _med_order(t, status="pending_verification")
    resp = nurse.post("/api/v1/hospital/nursing/mar/generate/", {"medication_order": str(pending.id)}, format="json")
    assert resp.status_code == 400


# ── Secure messaging ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_patient_and_care_team_message_each_other(mint_token, mock_jwks):
    from products.cymed.patient_portal.models import PatientPortalProfile

    t = uuid.uuid4()
    p, other = _patient(t), _patient(t)
    user = uuid.uuid4()
    PatientPortalProfile.objects.create(tenant_id=t, patient=p, user_id=user)
    me = _client(mint_token, t, roles=("patient",), sub=user, email="ada@x.io")
    staff = _client(mint_token, t, roles=("nurse",), email="rn@x.io")

    started = me.post("/api/v1/messages/my/threads/", {
        "subject": "Refill", "category": "prescription", "body": "Need my amlodipine refilled",
        "patient": str(other.id),  # ignored: a patient can only write about themselves
    }, format="json")
    assert started.status_code == 201, started.data
    assert started.data["patient"] == p.id
    tid = started.data["id"]

    inbox = _rows(staff.get("/api/v1/messages/threads/?status=open"))
    assert [r["id"] for r in inbox] == [tid] and inbox[0]["unread"] == 1
    detail = staff.get(f"/api/v1/messages/threads/{tid}/").data
    assert detail["messages"][0]["body"] == "Need my amlodipine refilled"
    assert _rows(staff.get("/api/v1/messages/threads/"))[0]["unread"] == 0  # opened → read
    assert staff.post(f"/api/v1/messages/threads/{tid}/reply/", {"body": "Sent to pharmacy"},
                      format="json").status_code == 201
    mine = _rows(me.get("/api/v1/messages/my/threads/"))
    assert mine[0]["unread"] == 1


@pytest.mark.django_db
def test_patient_cannot_read_another_patients_thread(mint_token, mock_jwks):
    from products.cymed.core.messaging.models import MessageThread
    from products.cymed.patient_portal.models import PatientPortalProfile

    t = uuid.uuid4()
    p, other = _patient(t), _patient(t)
    user = uuid.uuid4()
    PatientPortalProfile.objects.create(tenant_id=t, patient=p, user_id=user)
    theirs = MessageThread.objects.create(tenant_id=t, patient=other, subject="private")
    me = _client(mint_token, t, roles=("patient",), sub=user)
    assert _rows(me.get("/api/v1/messages/my/threads/")) == []
    assert me.get(f"/api/v1/messages/my/threads/{theirs.id}/").status_code == 404
    assert me.post(f"/api/v1/messages/my/threads/{theirs.id}/reply/", {"body": "hi"},
                   format="json").status_code == 404
    # and the staff inbox is closed to patients
    assert me.get("/api/v1/messages/threads/").status_code == 403
