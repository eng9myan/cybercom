import uuid
import pytest
from rest_framework.test import APIClient
import jwt

from platform.cyintegrationhub.models import IntegrationPartner, ConnectorConfig, TransformationMapping, MessageAuditLog
from platform.cyintegrationhub.services import TransformationEngine, MappingEngine, RoutingEngine, ConnectorFramework
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
            active=True
        )
        assert str(partner) == "Partner(Partner A, fhir)"

    def test_connector_config(self):
        partner = IntegrationPartner.objects.create(
            name="Partner B",
            slug="partner-b",
            protocol="hl7v2"
        )
        config = ConnectorConfig.objects.create(
            partner=partner,
            name="HL7 Endpoint",
            connector_type="hl7v2",
            endpoint_url="mllp://127.0.0.1:5000",
            sync_interval_seconds=60
        )
        assert str(config) == "Connector(HL7 Endpoint, hl7v2)"

    def test_transformation_mapping(self):
        mapping = TransformationMapping.objects.create(
            name="HL7 Patient Map",
            source_format="hl7v2",
            target_format="json",
            mapping_rules={"PID.3": "patient_id", "PID.5": "patient_name"}
        )
        assert str(mapping) == "Mapping(HL7 Patient Map: hl7v2 -> json)"

    def test_message_audit_log(self, test_tenant_id):
        partner = IntegrationPartner.objects.create(
            name="Partner C",
            slug="partner-c",
            protocol="soap"
        )
        log = MessageAuditLog.objects.create(
            tenant_id=test_tenant_id,
            partner=partner,
            connector_type="soap",
            direction="inbound",
            payload_size_bytes=500,
            status="success",
            duration_ms=120
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
            mapping_rules={"source_id": "target_id", "source_val": "target_val"}
        )
        source_data = {"source_id": "123", "source_val": "hello", "extra": "omit"}
        mapped = MappingEngine.map_fields(source_data, mapping)
        assert mapped == {"target_id": "123", "target_val": "hello"}

    def test_routing_engine(self, test_tenant_id):
        success = RoutingEngine.route_message(
            tenant_id=str(test_tenant_id),
            topic="platform.identity.events",
            event_type="cyidentity.user.provisioned",
            payload={"user_id": "usr-1"}
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
            payload={"id": "fhir-patient-1"}
        )
        assert res["fhir_status"] == "synced"
        assert MessageAuditLog.objects.filter(tenant_id=test_tenant_id, connector_type="fhir").count() == 1

    def test_hl7_connector(self, test_tenant_id):
        partner = IntegrationPartner.objects.create(name="P2", slug="p2", protocol="hl7")
        hl7_data = "MSH|^~\\&|||||||ADT^A08\rPID|||PID-1"
        res = ConnectorFramework.execute_connector(
            tenant_id=str(test_tenant_id),
            partner=partner,
            connector_type="hl7v2",
            action="receive",
            payload=hl7_data
        )
        assert res["hl7_status"] == "processed"
        assert res["data"]["patient_id"] == "PID-1"
        assert MessageAuditLog.objects.filter(tenant_id=test_tenant_id, direction="inbound").count() == 1

    def test_dicom_connector(self, test_tenant_id):
        partner = IntegrationPartner.objects.create(name="P3", slug="p3", protocol="dicom")
        res = ConnectorFramework.execute_connector(
            tenant_id=str(test_tenant_id),
            partner=partner,
            connector_type="dicom",
            action="send",
            payload="binary-dicom-data"
        )
        assert res["dicom_status"] == "archived"

    def test_ldap_connector(self, test_tenant_id):
        partner = IntegrationPartner.objects.create(name="P4", slug="p4", protocol="ldap")
        res = ConnectorFramework.execute_connector(
            tenant_id=str(test_tenant_id),
            partner=partner,
            connector_type="ldap",
            action="send",
            payload={"username": "admin"}
        )
        assert res["ldap_status"] == "authenticated"

    def test_smtp_connector(self, test_tenant_id):
        partner = IntegrationPartner.objects.create(name="P5", slug="p5", protocol="smtp")
        res = ConnectorFramework.execute_connector(
            tenant_id=str(test_tenant_id),
            partner=partner,
            connector_type="smtp",
            action="send",
            payload="Hello email"
        )
        assert res["smtp_status"] == "delivered"

    def test_soap_connector(self, test_tenant_id):
        partner = IntegrationPartner.objects.create(name="P6", slug="p6", protocol="soap")
        res = ConnectorFramework.execute_connector(
            tenant_id=str(test_tenant_id),
            partner=partner,
            connector_type="soap",
            action="send",
            payload="<soap>"
        )
        assert res["soap_status"] == "response_received"


@pytest.mark.django_db
class TestIntegrationAPIs:
    def test_list_partners(self, auth_client):
        partner = IntegrationPartner.objects.create(name="Partner X", slug="partner-x", protocol="fhir")
        resp = auth_client.get("/api/v1/integration/partners/")
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    def test_execute_connector_api(self, auth_client, test_tenant_id):
        partner = IntegrationPartner.objects.create(name="Partner Y", slug="partner-y", protocol="fhir")
        resp = auth_client.post(
            f"/api/v1/integration/partners/{partner.id}/execute/",
            {
                "tenant_id": str(test_tenant_id),
                "connector_type": "fhir",
                "action": "send",
                "payload": {"id": "patient-123"}
            },
            format="json"
        )
        assert resp.status_code == 200
        assert resp.data["fhir_status"] == "synced"
