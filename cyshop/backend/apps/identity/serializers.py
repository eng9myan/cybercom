import datetime
import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User, Role, Permission, PermissionGroup, RoleAssignment, UserProfile, UserSession, UserDevice
from apps.tenants.models import Tenant, Branch, Company

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    tenant_id = serializers.UUIDField(required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'tenant_id']

    def create(self, validated_data):
        tenant_id = validated_data.pop('tenant_id')
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            raise serializers.ValidationError({"tenant_id": "Tenant not found"})

        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.tenant_id = tenant.id
        user.save()

        # Create Profile
        UserProfile.objects.create(user=user, tenant_id=tenant.id)
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)
    user_id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    tenant_id = serializers.UUIDField(read_only=True)
    tenant_name = serializers.CharField(read_only=True)
    scopes = serializers.ListField(child=serializers.CharField(), read_only=True)

    def validate(self, data):
        username_or_email = data.get("username")
        password = data.get("password")

        # Support Email or Username login
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)
                username = user_obj.username
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid credentials")
        else:
            username = username_or_email

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials")

        tenant_id = str(user.tenant_id) if user.tenant_id else None
        tenant_name = ""
        if user.tenant_id:
            try:
                tenant = Tenant.objects.get(id=user.tenant_id)
                tenant_name = tenant.name
            except Tenant.DoesNotExist:
                pass

        # Fetch roles/scopes
        assignments = RoleAssignment.objects.filter(user=user)
        scopes = [a.role.code for a in assignments]

        # Generate JWT Access & Refresh Tokens
        access_payload = {
            "user_id": str(user.id),
            "username": user.username,
            "tenant_id": tenant_id,
            "scopes": scopes,
            "type": "access",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }
        refresh_payload = {
            "user_id": str(user.id),
            "type": "refresh",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }

        access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')

        # Track session
        from django.utils import timezone
        UserSession.objects.create(
            user=user,
            tenant_id=user.tenant_id,
            token=access_token,
            expires_at=timezone.now() + datetime.timedelta(hours=2)
        )

        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "tenant_id": user.tenant_id,
            "tenant_name": tenant_name,
            "scopes": scopes,
            "access_token": access_token,
            "refresh_token": refresh_token
        }

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'

class PermissionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionGroup
        fields = '__all__'

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class RoleAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleAssignment
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = '__all__'

class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active', 'tenant_id', 'created_at']
        read_only_fields = ['id', 'created_at']
