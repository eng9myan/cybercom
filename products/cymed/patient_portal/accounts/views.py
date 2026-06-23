from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import (
    PatientPortalAccount,
    PatientProfile,
    PatientPreferences,
    PatientSecuritySettings,
    PatientDevice,
)
from .serializers import (
    PatientPortalAccountSerializer,
    PatientPortalAccountDetailSerializer,
    PatientProfileSerializer,
    PatientPreferencesSerializer,
    PatientSecuritySettingsSerializer,
    PatientDeviceSerializer,
)


class PatientPortalAccountViewSet(viewsets.ModelViewSet):
    serializer_class = PatientPortalAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'phone']
    ordering_fields = ['created_at', 'last_login_at', 'username', 'account_status']
    ordering = ['-created_at']

    def get_queryset(self):
        return PatientPortalAccount.objects.filter(tenant_id=self.request.tenant_id)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PatientPortalAccountDetailSerializer
        return PatientPortalAccountSerializer

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        account = self.get_object()
        account.account_status = 'active'
        account.save(update_fields=['account_status', 'updated_at'])
        return Response({'status': 'Account activated.'})

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        account = self.get_object()
        account.account_status = 'suspended'
        account.save(update_fields=['account_status', 'updated_at'])
        return Response({'status': 'Account suspended.'})

    @action(detail=True, methods=['post'])
    def verify_email(self, request, pk=None):
        account = self.get_object()
        account.is_email_verified = True
        account.email_verified_at = timezone.now()
        account.save(update_fields=['is_email_verified', 'email_verified_at', 'updated_at'])
        return Response({'status': 'Email verified.'})

    @action(detail=True, methods=['post'])
    def verify_phone(self, request, pk=None):
        account = self.get_object()
        account.is_phone_verified = True
        account.phone_verified_at = timezone.now()
        account.save(update_fields=['is_phone_verified', 'phone_verified_at', 'updated_at'])
        return Response({'status': 'Phone verified.'})


class PatientProfileViewSet(viewsets.ModelViewSet):
    serializer_class = PatientProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'national_id', 'city']
    ordering_fields = ['created_at', 'last_name', 'first_name']
    ordering = ['last_name', 'first_name']

    def get_queryset(self):
        return PatientProfile.objects.filter(tenant_id=self.request.tenant_id)


class PatientPreferencesViewSet(viewsets.ModelViewSet):
    serializer_class = PatientPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return PatientPreferences.objects.filter(tenant_id=self.request.tenant_id)


class PatientSecuritySettingsViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSecuritySettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return PatientSecuritySettings.objects.filter(tenant_id=self.request.tenant_id)

    @action(detail=True, methods=['post'])
    def unlock(self, request, pk=None):
        settings_obj = self.get_object()
        settings_obj.failed_login_count = 0
        settings_obj.locked_until = None
        settings_obj.save(update_fields=['failed_login_count', 'locked_until', 'updated_at'])
        return Response({'status': 'Account unlocked.'})


class PatientDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = PatientDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['device_name', 'device_type', 'platform_version']
    ordering_fields = ['created_at', 'last_used_at', 'registered_at']
    ordering = ['-registered_at']

    def get_queryset(self):
        return PatientDevice.objects.filter(tenant_id=self.request.tenant_id)

    @action(detail=True, methods=['post'])
    def trust(self, request, pk=None):
        device = self.get_object()
        device.is_trusted = True
        device.save(update_fields=['is_trusted', 'updated_at'])
        return Response({'status': 'Device trusted.'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        device = self.get_object()
        device.is_active = False
        device.save(update_fields=['is_active', 'updated_at'])
        return Response({'status': 'Device deactivated.'})
