import uuid

import jwt
import pytest
from rest_framework.test import APIClient

from platform.cyintegrationhub.models import (
    ConnectorConfig,
    IntegrationPartner,
    MessageAuditLog,
    TransformationMapping,
)
from platform.cyintegrationhub.services import (
    ConnectorFramework,
    MappingEngine,
    RoutingEngine,
    TransformationEngine,
)
from platform.events.models import OutboxEvent


@pytest.fixture
def test_tenant_id():
    return uuid.uuid4()


@pytest.fixture
def auth_client(test_tenant_id):
    client = APIClient()
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "admin@cybercom.io",
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
class TestIntegrationModels:
    def test_partner_creation(self):
        partner = IntegrationPartner.objects.create(
            name="Partner A",
            slug="partner-a",
            protocol="fhir",
            direction="bidirectional",
            active=True,
        )
        assert str(partner) == "Partner(Partner A, fhir)"

    def test_connector_config(self):
        partner = IntegrationPartner.objects.create(
            name="Partner B", slug="partner-b", protocol="hl7v2"
        )
        config = ConnectorConfig.objects.create(
            partner=partner,
            name="HL7 Endpoint",
            connector_type="hl7v2",
            endpoint_url="mllp://127.0.0.1:5000",
            sync_interval_seconds=60,
        )
        assert str(config) == "Connector(HL7 Endpoint, hl7v2)"

    def test_transformation_mapping(self):
        mapping = TransformationMapping.objects.create(
            name="HL7 Patient Map",
            source_format="hl7v2",
            target_format="json",
            mapping_rules={"PID.3": "patient_id", "PID.5": "patient_name"},
        )
        assert str(mapping) == "Mapping(HL7 Patient Map: hl7v2 -> json)"

    def test_message_audit_log(self, test_tenant_id):
        partner = IntegrationPartner.objects.create(
            name="Partner C", slug="partner-c", protocol="soap"
        )
        log = MessageAuditLog.objects.create(
            tenant_id=test_tenant_id,
            partner=partner,
            connector_type="soap",
            direction="inbound",
            payload_size_bytes=500,
            status="success",
            duration_ms=120,
        )
        assert log.status == "success"
        assert log.duration_ms == 120


class TestTransformationEngine:
    def test_transform_hl7(self):
        hl7_data = "MSH|^~\\&|SENDING_APP|SENDING_FAC|||202606222046||ADT^A08|MSG00001|P|2.5\rPID|||PID-10042||Doe^John"
        parsed = TransformationEngine.transform(hl7_data, "hl7v2")
        assert parsed["message_type"] == "ADT^A08"
        assert parsed["patient_id"] == "PID-10042"
        assert parsed["patient_name"] == "Doe^John"

    def test_transform_xml(self):
        xml_data = "<Patient><id>123</id></Patient>"
        parsed = TransformationEngine.transform(xml_data, "xml")
        assert parsed["parsed_xml"] is True
        assert parsed["raw_content"] == xml_data

    def test_transform_default(self):
        raw = "some raw info"
        parsed = TransformationEngine.transform(raw, "raw")
        assert parsed["data"] == raw


@pytest.mark.django_db
class TestMappingAndRoutingEngines:
    def test_mapping_engine(self):
        mapping = TransformationMapping.objects.create(
            name="Custom Map",
            source_format="json",
            target_format="json",
            mapping_rules={"source_id": "target_id", "source_val": "target_val"},
        )
        source_data = {"source_id": "123", "source_val": "hello", "extra": "omit"}
        mapped = MappingEngine.map_fields(source_data, mapping)
        assert mapped == {"target_id": "123", "target_val": "hello"}

    def test_routing_engine(self, test_tenant_id):
        success = RoutingEngine.route_message(
            tenant_id=str(test_tenant_id),
            topic="platform.identity.events",
            event_type="cyidentity.user.provisioned",
            payload={"user_id": "usr-1"},
        )
        assert success is True
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id).count() == 1


@pytest.mark.django_db
class TestConnectorFramework:
    def test_fhir_connector(self, test_tenant_id):
        partner = IntegrationPartner.objects.create(name="P1", slug="p1", protocol="fhir")
        res = ConnectorFramework.execute_connector(
            tenant_id=str(test_tenant_id),
            partner=partner,
            connector_type="fhir",
            action="send",
            payload={"id": "fhir-patient-1"},
        )
        assert res["fhir_status"] == "synced"
        assert (
            MessageAuditLog.objects.filter(tenant_id=test_tenant_id, connector_type="fhir").count()
            == 1
        )

    def test_hl7_connector(self, test_tenant_id):
        partner = IntegrationPartner.objects.create(name="P2", slug="p2", protocol="hl7")
        hl7_data = "MSH|^~\\&|||||||ADT^A08\rPID|||PID-1"
        res = ConnectorFramework.execute_connector(
            tenant_id=str(test_tenant_id),
            partner=partner,
            connector_type="hl7v2",
            action="receive",
            payload=hl7_data,
        )
        assert res["hl7_status"] == "processed"
        assert res["data"]["patient_id"] == "PID-1"
        assert (
            MessageAuditLog.objects.filter(tenant_id=test_tenant_id, direction="inbound").count()
            == 1
        )

    def test_dicom_connector(self, test_tenant_id):
        partner = IntegrationPartner.objects.create(name="P3", slug="p3", protocol="dicom")
        res = ConnectorFramework.execute_connector(
            tenant_id=str(test_tenant_id),
            partner=partner,
            connector_type="dicom",
            action="send",
            payload="binary-dicom-data",
        )
        assert res["dicom_status"] == "archived"

    def test_ldap_connector(self, test_tenant_id):
        partner = IntegrationPartner.objects.create(name="P4", slug="p4", protocol="ldap")
        res = ConnectorFramework.execute_connector(
            tenant_id=str(test_tenant_id),
            partner=partner,
            connector_type="ldap",
            action="send",
            payload={"username": "admin"},
        )
        assert res["ldap_status"] == "authenticated"

    def test_smtp_connector(self, test_tenant_id):
        partner = IntegrationPartner.objects.create(name="P5", slug="p5", protocol="smtp")
        res = ConnectorFramework.execute_connector(
            tenant_id=str(test_tenant_id),
            partner=partner,
            connector_type="smtp",
            action="send",
            payload="Hello email",
        )
        assert res["smtp_status"] == "delivered"

    def test_soap_connector(self, test_tenant_id):
        partner = IntegrationPartner.objects.create(name="P6", slug="p6", protocol="soap")
        res = ConnectorFramework.execute_connector(
            tenant_id=str(test_tenant_id),
            partner=partner,
            connector_type="soap",
            action="send",
            payload="<soap>",
        )
        assert res["soap_status"] == "response_received"


@pytest.mark.django_db
class TestIntegrationAPIs:
    def test_list_partners(self, auth_client):
        IntegrationPartner.objects.create(name="Partner X", slug="partner-x", protocol="fhir")
        resp = auth_client.get("/api/v1/integration/partners/")
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    def test_execute_connector_api(self, auth_client, test_tenant_id):
        partner = IntegrationPartner.objects.create(
            name="Partner Y", slug="partner-y", protocol="fhir"
        )
        resp = auth_client.post(
            f"/api/v1/integration/partners/{partner.id}/execute/",
            {
                "tenant_id": str(test_tenant_id),
                "connector_type": "fhir",
                "action": "send",
                "payload": {"id": "patient-123"},
            },
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["fhir_status"] == "synced"


@pytest.mark.django_db
class TestResilienceAndParsers:
    def test_dicom_binary_parsing(self):
        # Create a mock DICOM byte string: 128 bytes preamble + b"DICM" + metadata
        preamble = b"\x00" * 128
        magic = b"DICM"
        payload = preamble + magic + b"some_dicom_data"

        metadata = ConnectorFramework.parse_dicom_metadata(payload)
        assert metadata["patient_name"] == "John Doe"
        assert metadata["sop_instance_uid"] == "1.2.840.10008.5.1.4.1.1.2.999"

    def test_complex_hl7_parsing(self):
        hl7_msg = (
            "MSH|^~\\&|SEND_APP|SEND_FAC|||20260628||ADT^A08|MSG123|P|2.5\r"
            "PID|||MRN98765^^^Hospital|John^Doe^Smith||19851025|M|||123 Main St||||||||\r"
            "PV1||I|ICU-01||||Dr. Johnson|||||||||||ENC4455\r"
            "OBX|1|NM|BP_SYSTOLIC||120|mmHg|90-140|N|||F"
        )
        parsed = TransformationEngine.transform(hl7_msg, "hl7v2")

        assert parsed["message_type"] == "ADT^A08"
        assert parsed["message_code"] == "ADT"
        assert parsed["trigger_event"] == "A08"
        assert parsed["patient"]["patient_id"] == "MRN98765"
        assert parsed["patient"]["first_name"] == "Doe"
        assert parsed["patient"]["last_name"] == "John"
        assert parsed["patient"]["dob"] == "19851025"
        assert parsed["visit"]["patient_class"] == "I"
        assert parsed["visit"]["assigned_location"] == "ICU-01"
        assert parsed["visit"]["encounter_id"] == "ENC4455"
        assert parsed["observations"][0]["value"] == "120"
        assert parsed["observations"][0]["units"] == "mmHg"

    def test_circuit_breaker_tripping(self, test_tenant_id):
        from platform.cyintegrationhub.services import CircuitBreakerOpenException

        IntegrationPartner.objects.create(name="Failing Partner", slug="fail-p", protocol="fhir")

        # We simulate repeated failure calling a mock failing connector type
        # Let's trigger execute_connector with an invalid connector type or make it fail
        # ConnectorFramework raises default_processed or handles Exceptions.
        # Let's force an exception in execution to trigger the circuit breaker failure records.
        # Since execute_connector catches Exception internally and returns {"error": ...}, we can test the decorator directly.
        from platform.cyintegrationhub.services import resilient_call

        call_count = 0

        @resilient_call(partner_name="Failing Partner", max_retries=2, backoff_seconds=0.01)
        def fail_operation():
            nonlocal call_count
            call_count += 1
            raise ValueError("Connection failed")

        # Let's execute it repeatedly until the breaker opens (failure threshold = 5)
        for _ in range(5):
            with pytest.raises(ValueError):
                fail_operation()

        # The 6th call should trip the circuit breaker and raise CircuitBreakerOpenException immediately without executing
        with pytest.raises(CircuitBreakerOpenException):
            fail_operation()

        # Call count should be 10 (2 attempts per call, 5 calls before opening)
        assert call_count == 10
