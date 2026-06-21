import time
import json
import logging

class AuditMiddleware:
    """
    Standard request logging middleware for observability.
    Captures latency, statuses, and endpoints.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("cybercom.api.audit")

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time

        audit_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "path": request.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_sec": round(duration, 4),
            "ip": request.META.get('REMOTE_ADDR'),
            "user_id": getattr(request, 'user_session', {}).get('user_id', 'anonymous'),
            "tenant_id": getattr(request, 'tenant_id', 'unknown')
        }

        self.logger.info(json.dumps(audit_data))
        return response
