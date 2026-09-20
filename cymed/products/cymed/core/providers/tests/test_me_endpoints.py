"""
The clinician SPA's Overview and My Patients screens are built on these three
new ProviderViewSet actions (me/me-dashboard/me-patients) — there was no
provider-scoped composed endpoint anywhere in the codebase before this.
"""
import uuid
from datetime import date, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cymed.ai_cds.models import CDSAlert
from products.cymed.clinic.telemedicine.models import VirtualVisit
from products.cymed.core.encounters.models import Encounter, EncounterParticipant
from products.cymed.core.facilities.models import Facility
from products.cymed.core.orders.models import Order, OrderStatus, OrderType
from products.cymed.core.organizations.models import Organization, OrganizationType
from products.cymed.core.patients.models import GenderType, Patient
from products.cymed.core.providers.models import Provider, ProviderType
from products.cymed.core.scheduling.models import (
    Appointment,
    AppointmentParticipant,
    AppointmentParticipantType,
)


def _auth_client(tenant_id, sub, mint_token, mock_jwks):
    client = APIClient()
    token = mint_token({
        "sub": sub,
        "email": "doctor@cymed.io",
        "tenant_id": str(tenant_id),
        "realm_access": {"roles": ["physician"]},
        "roles": ["physician"],
        "permissions": ["read", "write"],
    })
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant_id))
    return client


def _org_facility(tenant_id):
    org = Organization.objects.create(
        tenant_id=tenant_id, name="Org", slug=f"org-{uuid.uuid4()}",
        organization_type=OrganizationType.HOSPITAL,
    )
    facility = Facility.objects.create(
        tenant_id=tenant_id, organization=org, name="Main", code=f"FAC-{uuid.uuid4().hex[:8]}",
    )
    return org, facility


def _patient(tenant_id, active=True):
    return Patient.objects.create(
        tenant_id=tenant_id, first_name="Jane", last_name="Doe",
        dob=date(1990, 1, 1), gender=GenderType.FEMALE, mrn=f"MRN-{uuid.uuid4().hex[:8]}",
        is_active=active,
    )


def _encounter_with_provider(tenant_id, patient, provider, org, facility):
    encounter = Encounter.objects.create(
        tenant_id=tenant_id, patient=patient, organization=org, facility=facility,
        encounter_type="outpatient", status="planned",
    )
    EncounterParticipant.objects.create(
        tenant_id=tenant_id, encounter=encounter, provider=provider, role="attending",
    )
    return encounter


@pytest.mark.django_db
def test_me_404s_when_no_provider_linked(mint_token, mock_jwks):
    tenant_id = uuid.uuid4()
    resp = _auth_client(tenant_id, str(uuid.uuid4()), mint_token, mock_jwks).get(
        "/api/v1/providers/me/"
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_me_resolves_provider_by_session_user_id(mint_token, mock_jwks):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    provider = Provider.objects.create(
        tenant_id=tenant_id, user_id=user_id, first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-ME-1",
    )
    resp = _auth_client(tenant_id, str(user_id), mint_token, mock_jwks).get("/api/v1/providers/me/")
    assert resp.status_code == 200
    assert resp.data["id"] == str(provider.id) or resp.data["id"] == provider.id


@pytest.mark.django_db
def test_me_is_tenant_isolated(mint_token, mock_jwks):
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    user_id = uuid.uuid4()
    # A provider with this user_id exists only in tenant B.
    Provider.objects.create(
        tenant_id=tenant_b, user_id=user_id, first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-ISO-1",
    )
    resp = _auth_client(tenant_a, str(user_id), mint_token, mock_jwks).get("/api/v1/providers/me/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_dashboard_counts_are_real(mint_token, mock_jwks):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    provider = Provider.objects.create(
        tenant_id=tenant_id, user_id=user_id, first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-DASH-1",
    )
    org, facility = _org_facility(tenant_id)

    active_patient = _patient(tenant_id, active=True)
    inactive_patient = _patient(tenant_id, active=False)
    _encounter_with_provider(tenant_id, active_patient, provider, org, facility)
    _encounter_with_provider(tenant_id, inactive_patient, provider, org, facility)

    now = timezone.now()
    # today's appointment for this provider
    today_appt = Appointment.objects.create(
        tenant_id=tenant_id, patient=active_patient, appointment_type="checkup",
        start_time=now, end_time=now + timedelta(minutes=30),
    )
    AppointmentParticipant.objects.create(
        tenant_id=tenant_id, appointment=today_appt, actor_id=provider.id,
        actor_type=AppointmentParticipantType.PROVIDER,
    )
    # an appointment tomorrow must not count
    tomorrow_appt = Appointment.objects.create(
        tenant_id=tenant_id, patient=active_patient, appointment_type="checkup",
        start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, minutes=30),
    )
    AppointmentParticipant.objects.create(
        tenant_id=tenant_id, appointment=tomorrow_appt, actor_id=provider.id,
        actor_type=AppointmentParticipantType.PROVIDER,
    )

    Order.objects.create(
        tenant_id=tenant_id, patient=active_patient, order_type=OrderType.LABORATORY,
        status=OrderStatus.ACTIVE, ordered_by="dr-house",
    )
    # a completed order must not count as pending
    Order.objects.create(
        tenant_id=tenant_id, patient=active_patient, order_type=OrderType.LABORATORY,
        status=OrderStatus.COMPLETED, ordered_by="dr-house",
    )

    VirtualVisit.objects.create(
        tenant_id=tenant_id, patient=active_patient, provider_id=provider.id,
        scheduled_start=now, status="scheduled",
    )

    CDSAlert.objects.create(
        tenant_id=tenant_id, patient_id=active_patient.id, kind="fall_risk",
        severity="high", title="Fall risk", detail="",
    )
    # an already-acknowledged alert must not appear in recent_alerts
    CDSAlert.objects.create(
        tenant_id=tenant_id, patient_id=active_patient.id, kind="drug_allergy",
        severity="critical", title="Acked", detail="",
        acknowledged_at="2026-01-01T00:00:00Z",
    )

    resp = _auth_client(tenant_id, str(user_id), mint_token, mock_jwks).get(
        "/api/v1/providers/me/dashboard/"
    )
    assert resp.status_code == 200
    data = resp.data
    assert data["todays_appointments"] == 1
    assert data["active_patients"] == 1  # inactive patient excluded
    assert data["pending_results"] == 1  # completed order excluded
    assert data["telemedicine_queue"] == 1
    assert len(data["recent_alerts"]) == 1
    assert data["recent_alerts"][0]["title"] == "Fall risk"
    assert data["profile"] is None
    assert data["credentialing"] is None


@pytest.mark.django_db
def test_dashboard_is_tenant_isolated(mint_token, mock_jwks):
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    user_id = uuid.uuid4()
    provider_a = Provider.objects.create(
        tenant_id=tenant_a, user_id=user_id, first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-DASH-ISO-A",
    )
    org_b, facility_b = _org_facility(tenant_b)
    provider_b = Provider.objects.create(
        tenant_id=tenant_b, user_id=uuid.uuid4(), first_name="C", last_name="D",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-DASH-ISO-B",
    )
    patient_b = _patient(tenant_b)
    _encounter_with_provider(tenant_b, patient_b, provider_b, org_b, facility_b)

    resp = _auth_client(tenant_a, str(user_id), mint_token, mock_jwks).get(
        "/api/v1/providers/me/dashboard/"
    )
    assert resp.status_code == 200
    assert resp.data["active_patients"] == 0


@pytest.mark.django_db
def test_my_patients_roster(mint_token, mock_jwks):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    provider = Provider.objects.create(
        tenant_id=tenant_id, user_id=user_id, first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-ROSTER-1",
    )
    org, facility = _org_facility(tenant_id)
    my_patient = _patient(tenant_id)
    _encounter_with_provider(tenant_id, my_patient, provider, org, facility)

    other_provider = Provider.objects.create(
        tenant_id=tenant_id, user_id=uuid.uuid4(), first_name="X", last_name="Y",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-ROSTER-2",
    )
    not_my_patient = _patient(tenant_id)
    _encounter_with_provider(tenant_id, not_my_patient, other_provider, org, facility)

    resp = _auth_client(tenant_id, str(user_id), mint_token, mock_jwks).get(
        "/api/v1/providers/me/patients/"
    )
    assert resp.status_code == 200
    rows = resp.data.get("results", resp.data)
    assert len(rows) == 1
    assert rows[0]["mrn"] == my_patient.mrn


def _appointment_with_participant(tenant_id, patient, provider_id, start_time):
    appt = Appointment.objects.create(
        tenant_id=tenant_id, patient=patient, appointment_type="follow-up",
        start_time=start_time, end_time=start_time + timedelta(minutes=30),
    )
    AppointmentParticipant.objects.create(
        tenant_id=tenant_id, appointment=appt, actor_id=provider_id,
        actor_type=AppointmentParticipantType.PROVIDER,
    )
    return appt


@pytest.mark.django_db
def test_schedule_defaults_to_today(mint_token, mock_jwks):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    provider = Provider.objects.create(
        tenant_id=tenant_id, user_id=user_id, first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-SCHED-1",
    )
    patient = _patient(tenant_id)
    now = timezone.now()
    today_appt = _appointment_with_participant(tenant_id, patient, provider.id, now)
    _appointment_with_participant(tenant_id, patient, provider.id, now + timedelta(days=1))

    resp = _auth_client(tenant_id, str(user_id), mint_token, mock_jwks).get(
        "/api/v1/providers/me/schedule/"
    )
    assert resp.status_code == 200
    assert resp.data["date"] == str(date.today())
    assert len(resp.data["appointments"]) == 1
    assert resp.data["appointments"][0]["id"] == str(today_appt.id)
    assert resp.data["appointments"][0]["patient_name"] == "Jane Doe"


@pytest.mark.django_db
def test_schedule_respects_explicit_date(mint_token, mock_jwks):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    provider = Provider.objects.create(
        tenant_id=tenant_id, user_id=user_id, first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-SCHED-2",
    )
    patient = _patient(tenant_id)
    target = timezone.make_aware(timezone.datetime(2026, 8, 1, 9, 0))
    _appointment_with_participant(tenant_id, patient, provider.id, target)
    _appointment_with_participant(tenant_id, patient, provider.id, timezone.now())

    resp = _auth_client(tenant_id, str(user_id), mint_token, mock_jwks).get(
        "/api/v1/providers/me/schedule/?date=2026-08-01"
    )
    assert resp.status_code == 200
    assert resp.data["date"] == "2026-08-01"
    assert len(resp.data["appointments"]) == 1


@pytest.mark.django_db
def test_schedule_rejects_bad_date(mint_token, mock_jwks):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    Provider.objects.create(
        tenant_id=tenant_id, user_id=user_id, first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-SCHED-3",
    )
    resp = _auth_client(tenant_id, str(user_id), mint_token, mock_jwks).get(
        "/api/v1/providers/me/schedule/?date=not-a-date"
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_schedule_excludes_other_providers_appointments(mint_token, mock_jwks):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    provider = Provider.objects.create(
        tenant_id=tenant_id, user_id=user_id, first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-SCHED-4",
    )
    other_provider = Provider.objects.create(
        tenant_id=tenant_id, user_id=uuid.uuid4(), first_name="X", last_name="Y",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-SCHED-5",
    )
    patient = _patient(tenant_id)
    now = timezone.now()
    _appointment_with_participant(tenant_id, patient, other_provider.id, now)

    resp = _auth_client(tenant_id, str(user_id), mint_token, mock_jwks).get(
        "/api/v1/providers/me/schedule/"
    )
    assert resp.status_code == 200
    assert resp.data["appointments"] == []


@pytest.mark.django_db
def test_orders_aggregates_lab_and_imaging_for_this_provider(mint_token, mock_jwks):
    from products.cymed.imaging.orders.models import ImagingOrder
    from products.cymed.laboratory.orders.models import LabOrder

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    provider = Provider.objects.create(
        tenant_id=tenant_id, user_id=user_id, first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-ORD-1",
    )
    other_provider_id = uuid.uuid4()
    patient = _patient(tenant_id)

    LabOrder.objects.create(
        tenant_id=tenant_id, order_number=f"LAB-{uuid.uuid4().hex[:8]}", patient_id=patient.id,
        ordered_by=provider.id, status="submitted", priority="routine", clinical_notes="rule out anemia",
    )
    ImagingOrder.objects.create(
        tenant_id=tenant_id, order_number=f"IMG-{uuid.uuid4().hex[:8]}", patient_id=patient.id,
        ordered_by=provider.id, status="pending", priority="stat", order_type="outpatient",
        clinical_indication="suspected fracture",
    )
    # a different provider's lab order must not show up
    LabOrder.objects.create(
        tenant_id=tenant_id, order_number=f"LAB-{uuid.uuid4().hex[:8]}", patient_id=patient.id,
        ordered_by=other_provider_id, status="submitted", priority="routine", clinical_notes="n/a",
    )

    resp = _auth_client(tenant_id, str(user_id), mint_token, mock_jwks).get(
        "/api/v1/providers/me/orders/"
    )
    assert resp.status_code == 200
    orders = resp.data["orders"]
    assert len(orders) == 2
    kinds = {o["kind"] for o in orders}
    assert kinds == {"lab", "imaging"}
    for o in orders:
        assert o["patient_name"] == "Jane Doe"


@pytest.mark.django_db
def test_orders_includes_medication_orders_by_prescriber(mint_token, mock_jwks):
    from products.cymed.pharmacy.prescriptions.models import MedicationOrder

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    provider = Provider.objects.create(
        tenant_id=tenant_id, user_id=user_id, first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-ORD-2",
    )
    patient = _patient(tenant_id)

    MedicationOrder.objects.create(
        tenant_id=tenant_id, order_number=f"RX-{uuid.uuid4().hex[:8]}", patient_id=patient.id,
        admission_id=uuid.uuid4(), prescriber_id=provider.id, status="active", priority="routine",
        drug_code="RXN-1", drug_name="Amoxicillin", dose="500", dose_unit="mg", route="oral",
        frequency="tid",
    )

    resp = _auth_client(tenant_id, str(user_id), mint_token, mock_jwks).get(
        "/api/v1/providers/me/orders/"
    )
    assert resp.status_code == 200
    orders = resp.data["orders"]
    assert len(orders) == 1
    assert orders[0]["kind"] == "medication"
    assert orders[0]["label"] == "Amoxicillin"


@pytest.mark.django_db
def test_orders_is_tenant_isolated(mint_token, mock_jwks):
    from products.cymed.laboratory.orders.models import LabOrder

    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    user_id = uuid.uuid4()
    provider_a = Provider.objects.create(
        tenant_id=tenant_a, user_id=user_id, first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-ORD-3A",
    )
    patient_b = Patient.objects.create(
        tenant_id=tenant_b, first_name="X", last_name="Y", dob=date(1980, 1, 1),
        gender=GenderType.MALE, mrn=f"MRN-{uuid.uuid4().hex[:8]}",
    )
    # same provider id reused under tenant B on purpose — must not leak across tenants
    LabOrder.objects.create(
        tenant_id=tenant_b, order_number=f"LAB-{uuid.uuid4().hex[:8]}", patient_id=patient_b.id,
        ordered_by=provider_a.id, status="submitted", priority="routine", clinical_notes="n/a",
    )

    resp = _auth_client(tenant_a, str(user_id), mint_token, mock_jwks).get(
        "/api/v1/providers/me/orders/"
    )
    assert resp.status_code == 200
    assert resp.data["orders"] == []


@pytest.mark.django_db
def test_telemedicine_lists_this_providers_visits(mint_token, mock_jwks):
    from products.cymed.clinic.telemedicine.models import VirtualSession, VirtualVisit

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    provider = Provider.objects.create(
        tenant_id=tenant_id, user_id=user_id, first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-TM-1",
    )
    other_provider_id = uuid.uuid4()
    patient = _patient(tenant_id)

    with_session = VirtualVisit.objects.create(
        tenant_id=tenant_id, patient=patient, provider_id=provider.id,
        scheduled_start=timezone.now(), status="in_progress",
    )
    VirtualSession.objects.create(
        tenant_id=tenant_id, visit=with_session, session_token="tok",
        connection_url="https://meet.example/abc",
    )
    no_session = VirtualVisit.objects.create(
        tenant_id=tenant_id, patient=patient, provider_id=provider.id,
        scheduled_start=timezone.now(), status="scheduled",
    )
    # a different provider's visit must not show up
    VirtualVisit.objects.create(
        tenant_id=tenant_id, patient=patient, provider_id=other_provider_id,
        scheduled_start=timezone.now(), status="scheduled",
    )

    resp = _auth_client(tenant_id, str(user_id), mint_token, mock_jwks).get(
        "/api/v1/providers/me/telemedicine/"
    )
    assert resp.status_code == 200
    visits = {v["id"]: v for v in resp.data["visits"]}
    assert set(visits.keys()) == {str(with_session.id), str(no_session.id)}
    assert visits[str(with_session.id)]["connection_url"] == "https://meet.example/abc"
    assert visits[str(no_session.id)]["connection_url"] is None


@pytest.mark.django_db
def test_telemedicine_status_filter(mint_token, mock_jwks):
    from products.cymed.clinic.telemedicine.models import VirtualVisit

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    provider = Provider.objects.create(
        tenant_id=tenant_id, user_id=user_id, first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-TM-2",
    )
    patient = _patient(tenant_id)
    VirtualVisit.objects.create(
        tenant_id=tenant_id, patient=patient, provider_id=provider.id,
        scheduled_start=timezone.now(), status="completed",
    )
    scheduled = VirtualVisit.objects.create(
        tenant_id=tenant_id, patient=patient, provider_id=provider.id,
        scheduled_start=timezone.now(), status="scheduled",
    )

    resp = _auth_client(tenant_id, str(user_id), mint_token, mock_jwks).get(
        "/api/v1/providers/me/telemedicine/?status=scheduled"
    )
    assert resp.status_code == 200
    assert len(resp.data["visits"]) == 1
    assert resp.data["visits"][0]["id"] == str(scheduled.id)


@pytest.mark.django_db
def test_telemedicine_is_tenant_isolated(mint_token, mock_jwks):
    from products.cymed.clinic.telemedicine.models import VirtualVisit

    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    user_id = uuid.uuid4()
    provider_a = Provider.objects.create(
        tenant_id=tenant_a, user_id=user_id, first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi="NPI-TM-3A",
    )
    patient_b = Patient.objects.create(
        tenant_id=tenant_b, first_name="X", last_name="Y", dob=date(1980, 1, 1),
        gender=GenderType.MALE, mrn=f"MRN-{uuid.uuid4().hex[:8]}",
    )
    VirtualVisit.objects.create(
        tenant_id=tenant_b, patient=patient_b, provider_id=provider_a.id,
        scheduled_start=timezone.now(), status="scheduled",
    )

    resp = _auth_client(tenant_a, str(user_id), mint_token, mock_jwks).get(
        "/api/v1/providers/me/telemedicine/"
    )
    assert resp.status_code == 200
    assert resp.data["visits"] == []
