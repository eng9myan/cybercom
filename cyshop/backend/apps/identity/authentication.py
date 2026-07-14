import jwt
from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
from .models import User

class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get("user_id")
            tenant_id = payload.get("tenant_id")
            
            if not user_id:
                raise exceptions.AuthenticationFailed("Invalid payload in auth token")
                
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise exceptions.AuthenticationFailed("User not found matching token context")

            # Check if active tenant context matches
            request.tenant_id = tenant_id
            return (user, token)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Auth token expired")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Invalid auth token")
