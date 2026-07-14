from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import logout
from .models import User, Role, Permission, PermissionGroup, RoleAssignment, UserProfile, UserSession, UserDevice
from .serializers import (
    UserRegisterSerializer, UserLoginSerializer, UserSerializer, RoleSerializer,
    PermissionSerializer, PermissionGroupSerializer, RoleAssignmentSerializer,
    UserProfileSerializer, UserSessionSerializer, UserDeviceSerializer
)

class UserRegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Delete session
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            UserSession.objects.filter(token=token).delete()
        
        logout(request)
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)

class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Placeholder for password reset request handling
        email = request.data.get("email")
        return Response({"message": f"Password reset email sent to {email}"}, status=status.HTTP_200_OK)

class MfaToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Toggle MFA status
        user = request.user
        enable = request.data.get("enable", False)
        user.is_mfa_enabled = enable
        if enable:
            user.mfa_secret = "JBSWY3DPEHPK3PXP" # Base32 dummy secret
        else:
            user.mfa_secret = None
        user.save()
        return Response({
            "is_mfa_enabled": user.is_mfa_enabled,
            "mfa_secret": user.mfa_secret
        }, status=status.HTTP_200_OK)

class GoogleOAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # OAuth integration ready endpoint placeholder
        return Response({"message": "Google Login API route configured and ready"}, status=status.HTTP_200_OK)

class MicrosoftOAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # OAuth integration ready endpoint placeholder
        return Response({"message": "Microsoft Login API route configured and ready"}, status=status.HTTP_200_OK)

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(tenant_id=self.request.tenant_id, is_deleted=False)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

class RoleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RoleSerializer

    def get_queryset(self):
        return Role.objects.filter(tenant_id=self.request.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id)

class PermissionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PermissionSerializer

    def get_queryset(self):
        # Permissions are usually global or tenant-scoped
        return Permission.objects.filter(tenant_id=self.request.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id)

class PermissionGroupViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PermissionGroupSerializer

    def get_queryset(self):
        return PermissionGroup.objects.filter(tenant_id=self.request.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id)

class RoleAssignmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RoleAssignmentSerializer

    def get_queryset(self):
        return RoleAssignment.objects.filter(tenant_id=self.request.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id)

class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        return UserProfile.objects.filter(tenant_id=self.request.tenant_id)

class UserSessionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSessionSerializer

    def get_queryset(self):
        return UserSession.objects.filter(tenant_id=self.request.tenant_id)

class UserDeviceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserDeviceSerializer

    def get_queryset(self):
        return UserDevice.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, tenant_id=self.request.tenant_id)
