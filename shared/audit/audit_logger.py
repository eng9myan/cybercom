import logging
import json
import time

class CyAuditLogger:
    """
    Unified JSON audit logging formatter for all Python applications.
    Ensures conformance with ADR-0028.
    """
    def __init__(self, service_name):
        self.logger = logging.getLogger(f"cybercom.audit.{service_name}")
        self.logger.setLevel(logging.INFO)
        # Prevent double logging
        self.logger.propagate = False
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            self.logger.addHandler(handler)

    def log_event(self, tenant_id, user_id, action, resource, status, details=None):
        audit_payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tenant_id": tenant_id,
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "status": status,
            "details": details or {}
        }
        # Emits structured JSON directly to stdout/syslog for log collectors (fluentbit/vector)
        self.logger.info(json.dumps(audit_payload))
