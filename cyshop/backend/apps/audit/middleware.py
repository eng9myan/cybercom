from .models import SystemAuditLog

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Log requests that modify data (POST, PUT, DELETE, PATCH)
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH'] and response.status_code < 400:
            tenant_id = getattr(request, 'tenant_id', None)
            user_id = getattr(request.user, 'id', None) if request.user and request.user.is_authenticated else None
            username = getattr(request.user, 'username', None) if request.user and request.user.is_authenticated else 'anonymous'
            
            # Resolve IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')

            action = f"API Request: {request.method} {request.path}"
            
            SystemAuditLog.objects.create(
                tenant_id=tenant_id,
                user_id=user_id,
                username=username,
                action=action,
                ip_address=ip,
                method=request.method,
                path=request.path
            )

        return response
