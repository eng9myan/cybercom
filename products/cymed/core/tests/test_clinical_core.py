import uuid

import jwt
import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from platform.events.models import OutboxEvent
from products.cymed.core.encounters.models import Encounter
from products.cymed.core.facilities.models import Bed, Department, Facility, Room, Ward
from products.cymed.core.organizations.models import Organization
from products.cymed.core.patients.models import Patient
from products.cymed.core.patients.services import PatientService
from products.cymed.core.providers.models import Provider
from products.cymed.core.registries.models import CohortRegistry, RegistryEntry


@pytest.fixture
def test_tenant_id():
    return uuid.uuid4()


@pytest.fixture
def auth_client(test_tenant_id):
    client = APIClient()
    payload = {
        "sub": "33333333-3333-3333-3333-333333333333",
        "email": "nurse@cymed.io",
        "tenant_id": str(test_tenant_id),
        "realm_access": {"roles": ["platform_admin"]},
        "roles": ["platform_admin"],
        "permissions": ["read", "write"],
    }
    token = jwt.encode(payload, "dummy-secret", algorithm="HS256")
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_X_TENANT_ID=str(test_tenant_id),
    )
    return client


@pytest.mark.django_db
class TestPatientsModule:
    def test_patient_creation_and_mrn(self, auth_client, test_tenant_id):
        # Test creation via endpoint
        response = auth_client.post(
            "/api/v1/patients/",
            {
                "first_name": "Ahmad",
                "last_name": "Yaseen",
                "dob": "1990-05-15",
                "gender": "male",
                "national_id": "1111222233",
                "identifiers": [{"system": "national-id", "value": "1111222233"}],
            },
            format="json",
        )
        assert response.status_code == 201
        assert "mrn" in response.data
        assert response.data["first_name"] == "Ahmad"

        # Verify database
        patient = Patient.objects.get(id=response.data["id"])
        assert patient.tenant_id == test_tenant_id
        assert patient.mrn.startswith("MRN-")

        # Verify created event in outbox
        events = OutboxEvent.objects.filter(
            tenant_id=test_tenant_id, event_type="cymed.patient.created"
        )
        assert events.count() == 1

    def test_duplicate_detection(self, test_tenant_id):
        # Create baseline patient
        p1 = Patient.objects.create(
            tenant_id=test_tenant_id,
            first_name="Khaled",
            last_name="Omar",
            dob="1985-08-20",
            mrn="MRN-88888",
            national_id="99998888",
        )

        # 1. Duplicate detection by national ID
        dupes_id = PatientService.detect_duplicates(
            first_name="Khaled",
            last_name="Omar",
            dob="1985-08-20",
            tenant_id=str(test_tenant_id),
            national_id="99998888",
        )
        assert dupes_id.count() == 1
        assert dupes_id.first() == p1

        # 2. Duplicate detection by fuzzy match (name + DOB)
        dupes_fuzzy = PatientService.detect_duplicates(
            first_name="Khalil", last_name="Omara", dob="1985-08-20", tenant_id=str(test_tenant_id)
        )
        assert dupes_fuzzy.count() == 1

    def test_patient_merge_and_unmerge(self, auth_client, test_tenant_id):
        p1 = Patient.objects.create(
            tenant_id=test_tenant_id,
            first_name="Ahmad 1",
            last_name="Ali",
            dob="1990-01-01",
            mrn="MRN-111",
        )
        p2 = Patient.objects.create(
            tenant_id=test_tenant_id,
            first_name="Ahmad 2",
            last_name="Ali",
            dob="1990-01-01",
            mrn="MRN-222",
        )

        # Trigger merge via API
        response = auth_client.post(
            "/api/v1/patients/merge/",
            {"source_patient_id": str(p1.id), "target_patient_id": str(p2.id)},
            format="json",
        )
        assert response.status_code == 200
        assert "merge_history_id" in response.data

        p1.refresh_from_db()
        p2.refresh_from_db()
        assert p1.is_active is False
        assert p1.merged_into == p2

        # Verify merge event
        assert (
            OutboxEvent.objects.filter(
                tenant_id=test_tenant_id, event_type="cymed.patient.merged"
            ).count()
            == 1
        )

        # Trigger unmerge via API
        hist_id = response.data["merge_history_id"]
        response_unmerge = auth_client.post(
            "/api/v1/patients/unmerge/", {"merge_history_id": hist_id}, format="json"
        )
        assert response_unmerge.status_code == 200

        p1.refresh_from_db()
        assert p1.is_active is True
        assert p1.merged_into is None

        # Verify unmerge event
        assert (
            OutboxEvent.objects.filter(
                tenant_id=test_tenant_id, event_type="cymed.patient.unmerged"
            ).count()
            == 1
        )


@pytest.mark.django_db
class TestProvidersModule:
    def test_provider_creation(self, auth_client, test_tenant_id):
        response = auth_client.post(
            "/api/v1/providers/",
            {
                "user_id": str(uuid.uuid4()),
                "first_name": "Dr. Mohammad",
                "last_name": "Al-Masri",
                "provider_type": "physician",
                "npi": "NPI-998877",
                "specialties": [
                    {"specialty_code": "cardiology", "specialty_display": "Cardiology"}
                ],
                "licenses": [
                    {
                        "license_number": "LIC-12345",
                        "state_issued": "Amman",
                        "expiry_date": "2030-12-31",
                    }
                ],
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["first_name"] == "Dr. Mohammad"

        provider = Provider.objects.get(id=response.data["id"])
        assert provider.specialties.count() == 1
        assert provider.licenses.count() == 1

        # Verify event
        assert (
            OutboxEvent.objects.filter(
                tenant_id=test_tenant_id, event_type="cymed.provider.created"
            ).count()
            == 1
        )


@pytest.mark.django_db
class TestOrganizationsAndFacilities:
    def test_organizations_and_facility_topology(self, auth_client, test_tenant_id):
        # Create organization
        org = Organization.objects.create(
            tenant_id=test_tenant_id,
            name="Amman Care Hospital",
            slug="amman-care-hospital",
            organization_type="hospital",
        )
        assert org.name == "Amman Care Hospital"

        # Create Facility
        fac = Facility.objects.create(
            tenant_id=test_tenant_id, organization=org, name="Main Campus", code="FAC-MAIN"
        )
        assert fac.code == "FAC-MAIN"

        # Topology structures
        dept = Department.objects.create(
            tenant_id=test_tenant_id, facility=fac, name="Emergency Department", code="DEPT-ER"
        )
        ward = Ward.objects.create(
            tenant_id=test_tenant_id, department=dept, name="ICU Ward", code="WARD-ICU"
        )
        room = Room.objects.create(
            tenant_id=test_tenant_id, ward=ward, room_number="ICU-101", room_type="icu"
        )
        bed = Bed.objects.create(
            tenant_id=test_tenant_id, room=room, bed_number="Bed-A", status="available"
        )
        assert bed.status == "available"


@pytest.mark.django_db
class TestEncountersModule:
    def test_encounter_workflow(self, auth_client, test_tenant_id):
        patient = Patient.objects.create(
            tenant_id=test_tenant_id,
            first_name="Ali",
            last_name="Hassan",
            dob="1975-03-12",
            mrn="MRN-777",
        )
        org = Organization.objects.create(
            tenant_id=test_tenant_id,
            name="Royal Rehab",
            slug="royal-rehab",
            organization_type="clinic",
        )
        fac = Facility.objects.create(
            tenant_id=test_tenant_id, organization=org, name="Rehab Facility", code="FAC-REHAB"
        )

        # Create encounter
        response = auth_client.post(
            "/api/v1/encounters/",
            {
                "patient": str(patient.id),
                "encounter_type": "outpatient",
                "status": "planned",
                "organization": str(org.id),
                "facility": str(fac.id),
            },
            format="json",
        )
        assert response.status_code == 201
        enc_id = response.data["id"]

        # Start encounter
        response_start = auth_client.post(f"/api/v1/encounters/{enc_id}/start/", format="json")
        assert response_start.status_code == 200
        assert response_start.data["status"] == "in_progress"
        assert (
            OutboxEvent.objects.filter(
                tenant_id=test_tenant_id, event_type="cymed.encounter.started"
            ).count()
            == 1
        )

        # Close encounter
        response_close = auth_client.post(f"/api/v1/encounters/{enc_id}/close/", format="json")
        assert response_close.status_code == 200
        assert response_close.data["status"] == "finished"
        assert (
            OutboxEvent.objects.filter(
                tenant_id=test_tenant_id, event_type="cymed.encounter.closed"
            ).count()
            == 1
        )


@pytest.mark.django_db
class TestClinicalModule:
    def test_condition_terminology_validation(self, auth_client, test_tenant_id):
        patient = Patient.objects.create(
            tenant_id=test_tenant_id,
            first_name="Saeed",
            last_name="Salem",
            dob="1960-06-30",
            mrn="MRN-333",
        )

        # Test condition creation with VALID ICD-11 code (FA81 exists in ICD11Provider mock)
        response_valid = auth_client.post(
            "/api/v1/clinical/conditions/",
            {
                "patient": str(patient.id),
                "code": "FA81",
                "display": "Osteoarthritis of knee",
                "system": "icd11",
                "clinical_status": "active",
                "verification_status": "confirmed",
                "recorded_by": "Dr. Salem",
            },
            format="json",
        )
        assert response_valid.status_code == 201

        # Test condition creation with INVALID ICD-11 code (should fail terminology validation)
        response_invalid = auth_client.post(
            "/api/v1/clinical/conditions/",
            {
                "patient": str(patient.id),
                "code": "INVALID-CODE",
                "display": "Fake Disease",
                "system": "icd11",
                "clinical_status": "active",
                "verification_status": "confirmed",
                "recorded_by": "Dr. Salem",
            },
            format="json",
        )
        assert response_invalid.status_code == 400
        assert "code" in response_invalid.data

    def test_vitals_and_observations(self, auth_client, test_tenant_id):
        patient = Patient.objects.create(
            tenant_id=test_tenant_id,
            first_name="Dana",
            last_name="Zaid",
            dob="1995-10-10",
            mrn="MRN-444",
        )
        org = Organization.objects.create(
            tenant_id=test_tenant_id,
            name="Royal Rehab",
            slug="royal-rehab-2",
            organization_type="clinic",
        )
        fac = Facility.objects.create(
            tenant_id=test_tenant_id, organization=org, name="Rehab Facility", code="FAC-REHAB-2"
        )
        enc = Encounter.objects.create(
            tenant_id=test_tenant_id,
            patient=patient,
            encounter_type="outpatient",
            status="in_progress",
            organization=org,
            facility=fac,
        )

        # Create Vital Sign
        response_vital = auth_client.post(
            "/api/v1/clinical/vitals/",
            {
                "patient": str(patient.id),
                "encounter": str(enc.id),
                "type": "heart_rate",
                "value": 75.00,
                "unit": "bpm",
                "taken_by": "Nurse Rania",
            },
            format="json",
        )
        assert response_vital.status_code == 201

        # Create Observation
        response_obs = auth_client.post(
            "/api/v1/clinical/observations/",
            {
                "patient": str(patient.id),
                "encounter": str(enc.id),
                "code": "2339-0",  # Blood Glucose
                "display": "Glucose in Blood",
                "value_quantity": 95.0000,
                "unit": "mg/dL",
                "status": "final",
            },
            format="json",
        )
        assert response_obs.status_code == 201


@pytest.mark.django_db
class TestClinicalDocumentation:
    def test_clinical_document_signatures(self, auth_client, test_tenant_id):
        patient = Patient.objects.create(
            tenant_id=test_tenant_id,
            first_name="Rami",
            last_name="Fadi",
            dob="1982-11-12",
            mrn="MRN-555",
        )

        response = auth_client.post(
            "/api/v1/documents/",
            {
                "patient": str(patient.id),
                "title": "SOAP Consultation Note",
                "document_type": "soap",
                "status": "draft",
                "content": "Patient details",
                "soap_note": {
                    "subjective": "Headache",
                    "objective": "Normal BP",
                    "assessment": "Stress",
                    "plan": "Rest",
                },
            },
            format="json",
        )
        assert response.status_code == 201
        doc_id = response.data["id"]

        # Sign document
        response_sign = auth_client.post(f"/api/v1/documents/{doc_id}/sign/", format="json")
        assert response_sign.status_code == 200
        assert response_sign.data["status"] == "final"
        assert response_sign.data["signed_by"] is not None

        # Verify event
        assert (
            OutboxEvent.objects.filter(
                tenant_id=test_tenant_id, event_type="cymed.document.signed"
            ).count()
            == 1
        )


@pytest.mark.django_db
class TestBreakGlassSecurity:
    def test_breakglass_emergency_grant(self, auth_client, test_tenant_id):
        # Post breakglass request
        response = auth_client.post(
            "/api/v1/clinical/breakglass/",
            {
                "patient_id": str(uuid.uuid4()),
                "reason": "clinical",
                "justification": "Patient unconscious in ER, immediate records audit required.",
            },
            format="json",
        )
        assert response.status_code == 200
        assert "session_expiry" in response.data

        # Verify event published
        assert (
            OutboxEvent.objects.filter(
                tenant_id=test_tenant_id, event_type="cymed.breakglass.used"
            ).count()
            == 1
        )


@pytest.mark.django_db
class TestRemainingClinicalFoundations:
    def test_careplans_orders_scheduling_consents_registries(self, auth_client, test_tenant_id):
        patient = Patient.objects.create(
            tenant_id=test_tenant_id,
            first_name="Lina",
            last_name="Mazen",
            dob="2000-01-01",
            mrn="MRN-666",
        )

        # 1. CarePlan
        cp_response = auth_client.post(
            "/api/v1/careplans/",
            {
                "patient": str(patient.id),
                "title": "Diabetes Care Path",
                "status": "active",
                "goals": [{"description": "Maintain HbA1c < 7%"}],
                "tasks": [{"title": "Check Blood Sugar Daily"}],
            },
            format="json",
        )
        assert cp_response.status_code == 201
        assert (
            OutboxEvent.objects.filter(
                tenant_id=test_tenant_id, event_type="cymed.careplan.created"
            ).count()
            == 1
        )

        # 2. Orders
        order_response = auth_client.post(
            "/api/v1/orders/",
            {
                "patient": str(patient.id),
                "order_type": "laboratory",
                "priority": "routine",
                "status": "active",
                "ordered_by": "Dr. Mazen",
                "items": [{"code": "2339-0", "display": "Glucose", "quantity": 1}],
            },
            format="json",
        )
        assert order_response.status_code == 201
        assert (
            OutboxEvent.objects.filter(
                tenant_id=test_tenant_id, event_type="cymed.order.created"
            ).count()
            == 1
        )

        # 3. Scheduling
        appt_response = auth_client.post(
            "/api/v1/scheduling/",
            {
                "patient": str(patient.id),
                "appointment_type": "checkup",
                "status": "booked",
                "start_time": timezone.now().isoformat(),
                "end_time": (timezone.now() + timezone.timedelta(minutes=30)).isoformat(),
                "participants": [{"actor_id": str(patient.id), "actor_type": "patient"}],
            },
            format="json",
        )
        assert appt_response.status_code == 201
        appt_id = appt_response.data["id"]

        # Cancel appointment
        cancel_resp = auth_client.post(f"/api/v1/scheduling/{appt_id}/cancel/", format="json")
        assert cancel_resp.status_code == 200
        assert (
            OutboxEvent.objects.filter(
                tenant_id=test_tenant_id, event_type="cymed.appointment.cancelled"
            ).count()
            == 1
        )

        # 4. Consents
        consent_response = auth_client.post(
            "/api/v1/consents/",
            {
                "patient": str(patient.id),
                "category": "treatment",
                "policy_rule": "Standard surgery consent",
                "signature": {"signatory_name": "Lina Mazen"},
            },
            format="json",
        )
        assert consent_response.status_code == 201
        assert (
            OutboxEvent.objects.filter(
                tenant_id=test_tenant_id, event_type="cymed.consent.created"
            ).count()
            == 1
        )

        # 5. Cohort Registries
        cohort = CohortRegistry.objects.create(
            tenant_id=test_tenant_id, name="Diabetes Registry", code="diabetes-registry"
        )
        entry = RegistryEntry.objects.create(
            tenant_id=test_tenant_id, registry=cohort, patient=patient, status="active"
        )
        assert entry.status == "active"
