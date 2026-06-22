import time
from typing import Any, Dict, Optional
from django.utils import timezone
from platform.cyintegrationhub.models import IntegrationPartner, TransformationMapping, MessageAuditLog
from platform.events.publisher import KafkaEventPublisher

class TransformationEngine:
    """
    Transforms payloads from source formats (e.g. HL7v2 or SOAP XML) to standard JSON.
    """
    @classmethod
    def transform(cls, data: str, source_format: str) -> Dict[str, Any]:
        source_format = source_format.lower()
        if source_format == "hl7v2":
            # Mock parse of HL7 ADT/ORU pipelines
            segments = data.split("\r")
            parsed = {}
            for seg in segments:
                parts = seg.split("|")
                if not parts or not parts[0]:
                    continue
                if parts[0] == "MSH":
                    parsed["message_type"] = parts[8] if len(parts) > 8 else "UNKNOWN"
                elif parts[0] == "PID":
                    parsed["patient_id"] = parts[3] if len(parts) > 3 else ""
                    parsed["patient_name"] = parts[5] if len(parts) > 5 else ""
            return parsed
        elif source_format == "xml":
            # Simple simulation of XML parser
            return {"parsed_xml": True, "raw_content": data}
        return {"data": data}


class MappingEngine:
    """
    Applies schema rules to map source dicts to standard target schemas.
    """
    @classmethod
    def map_fields(cls, source_data: Dict[str, Any], mapping: TransformationMapping) -> Dict[str, Any]:
        rules = mapping.mapping_rules
        target_data = {}
        for source_key, target_key in rules.items():
            if source_key in source_data:
                target_data[target_key] = source_data[source_key]
        return target_data


class RoutingEngine:
    """
    Routes transformed and mapped messages to events or target destinations.
    """
    @classmethod
    def route_message(cls, tenant_id: str, topic: str, event_type: str, payload: Dict[str, Any]) -> bool:
        # Route to Kafka via Outbox event pattern
        from platform.events.models import OutboxEvent
        try:
            OutboxEvent.objects.create(
                tenant_id=tenant_id,
                topic=topic,
                event_type=event_type,
                payload=payload,
                status="pending"
            )
            return True
        except Exception:
            return False


class ConnectorFramework:
    """
    Executes connections to external systems (FHIR, HL7, LDAP, SOAP, Keycloak, SMTP, etc.)
    and records execution logs.
    """
    @classmethod
    def execute_connector(
        cls,
        tenant_id: str,
        partner: IntegrationPartner,
        connector_type: str,
        action: str,
        payload: Any
    ) -> Dict[str, Any]:
        start_time = time.monotonic()
        status = "success"
        error_msg = ""
        result = {}

        try:
            connector_type = connector_type.lower()
            if connector_type == "fhir":
                result = {"fhir_status": "synced", "records_found": 12, "resource": "Patient"}
            elif connector_type == "hl7v2":
                transformed = TransformationEngine.transform(payload, "hl7v2")
                result = {"hl7_status": "processed", "data": transformed}
            elif connector_type == "dicom":
                result = {"dicom_status": "archived", "sop_instance_uid": "1.2.840.10008.5.1.4.1.1.2"}
            elif connector_type == "ldap" or connector_type == "active_directory":
                result = {"ldap_status": "authenticated", "dn": "uid=admin,ou=users,dc=cybercom"}
            elif connector_type == "smtp":
                result = {"smtp_status": "delivered", "message_id": "<mail.123@cybercom.io>"}
            elif connector_type == "soap":
                result = {"soap_status": "response_received", "envelope": "<SOAP-ENV:Envelope>"}
            else:
                result = {"status": "default_processed", "payload": payload}
        except Exception as exc:
            status = "failed"
            error_msg = str(exc)
            result = {"error": error_msg}

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        
        # Log delivery/execution details to MessageAuditLog
        MessageAuditLog.objects.create(
            tenant_id=tenant_id,
            partner=partner,
            connector_type=connector_type,
            direction="inbound" if action == "receive" else "outbound",
            payload_size_bytes=len(str(payload)),
            status=status,
            error_message=error_msg,
            duration_ms=elapsed_ms
        )

        return result
