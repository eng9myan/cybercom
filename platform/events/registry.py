from typing import Any, Dict

# Event Catalog & Schema Mappings (Program 2.5 Event Governance)
EVENT_TOPIC_REGISTRY: Dict[str, str] = {
    # System & Core Control Plane
    "cyidentity": "platform.identity.events",
    "tenant": "platform.tenant.events",
    "audit": "platform.audit.events",
    "api": "platform.api.gateway.events",
    
    # Products
    "cymed": "product.cymed.clinical.events",
    "cycom": "product.cycom.erp.events",
    "cyshop": "product.cyshop.retail.events",
    "cygov": "product.cygov.governance.events",
    "cyconnect": "product.cyconnect.comms.events",
    "cycitizen": "product.cycitizen.citizen.events",
    
    # Data & AI
    "cydata": "platform.cydata.lakehouse.events",
    "cyai": "platform.cyai.inference.events",
}

EVENT_SCHEMAS: Dict[str, Dict[str, Any]] = {
    # CyIdentity Events
    "cyidentity.user.provisioned": {
        "fields": ["user_id", "username", "email", "realm", "timestamp"]
    },
    "cyidentity.user.locked": {
        "fields": ["user_id", "username", "reason", "locked_until", "timestamp"]
    },
    "cyidentity.secret.rotated": {
        "fields": ["client_id", "secret_hint", "rotated_at", "timestamp"]
    },
    
    # Tenant Events
    "tenant.provisioned": {
        "fields": ["tenant_id", "name", "plan", "region", "timestamp"]
    },
    "tenant.suspended": {
        "fields": ["tenant_id", "reason", "suspended_at", "timestamp"]
    },
    
    # Audit Events
    "audit.log.emitted": {
        "fields": ["log_id", "tenant_id", "action", "resource_type", "timestamp"]
    },
    
    # CyMed Clinical Events
    "cymed.patient.admission": {
        "fields": ["patient_id", "encounter_id", "facility_id", "acuity_level", "timestamp"]
    },
    "cymed.prescription.written": {
        "fields": ["prescription_id", "patient_id", "physician_id", "medications", "timestamp"]
    },
    
    # CyCom ERP Events
    "cycom.transaction.approved": {
        "fields": ["transaction_id", "ledger_id", "amount", "currency", "timestamp"]
    },
    
    # CyAI Inference Events
    "cyai.prompt.evaluated": {
        "fields": ["log_id", "model_id", "prompt_hash", "tokens_spent", "safety_verdict", "timestamp"]
    }
}

class EventRegistry:
    @classmethod
    def get_topic_for_source(cls, source: str) -> str:
        return EVENT_TOPIC_REGISTRY.get(source.lower(), f"platform.{source.lower()}.general.events")

    @classmethod
    def validate_event(cls, event_type: str, payload: dict) -> bool:
        schema = EVENT_SCHEMAS.get(event_type)
        if not schema:
            # Fallback for dynamic events
            return True
        for field in schema["fields"]:
            if field not in payload:
                return False
        return True
