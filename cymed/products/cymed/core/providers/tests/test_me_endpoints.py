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
