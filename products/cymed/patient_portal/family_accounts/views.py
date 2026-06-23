from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import (
    FamilyGroup,
    FamilyMember,
    FamilyAccessPermission,
    DependentProfile,
)
from .serializers import (
    FamilyGroupSerializer,
    FamilyGroupDetailSerializer,
    FamilyMemberSerializer,
    FamilyMemberDetailSerializer,
    FamilyAccessPermissionSerializer,
    DependentProfileSerializer,
)


class FamilyGroupViewSet(viewsets.ModelViewSet):
    serializer_class = FamilyGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['group_name']
    ordering_fields = ['created_at', 'group_name']
    ordering = ['-created_at']

    def get_queryset(self):
        return FamilyGroup.objects.filter(tenant_id=self.request.tenant_id)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FamilyGroupDetailSerializer
        return FamilyGroupSerializer

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        group = self.get_object()
        group.is_active = False
        group.save(update_fields=['is_active', 'updated_at'])
        return Response({'status': 'Family group deactivated.'})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        group = self.get_object()
        group.is_active = True
        group.save(update_fields=['is_active', 'updated_at'])
        return Response({'status': 'Family group activated.'})


class FamilyMemberViewSet(viewsets.ModelViewSet):
    serializer_class = FamilyMemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'relationship']
    ordering_fields = ['created_at', 'last_name', 'first_name', 'relationship']
    ordering = ['last_name', 'first_name']

    def get_queryset(self):
        qs = FamilyMember.objects.filter(tenant_id=self.request.tenant_id)
        group_id = self.request.query_params.get('group')
        relationship = self.request.query_params.get('relationship')
        is_minor = self.request.query_params.get('is_minor')
        is_active = self.request.query_params.get('is_active')
        if group_id:
            qs = qs.filter(group_id=group_id)
        if relationship:
            qs = qs.filter(relationship=relationship)
        if is_minor is not None:
            qs = qs.filter(is_minor=is_minor.lower() == 'true')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FamilyMemberDetailSerializer
        return FamilyMemberSerializer

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        member = self.get_object()
        member.is_active = False
        member.save(update_fields=['is_active', 'updated_at'])
        return Response({'status': 'Family member deactivated.'})


class FamilyAccessPermissionViewSet(viewsets.ModelViewSet):
    serializer_class = FamilyAccessPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'valid_from', 'valid_until']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = FamilyAccessPermission.objects.filter(tenant_id=self.request.tenant_id)
        grantor = self.request.query_params.get('grantor_account_id')
        grantee = self.request.query_params.get('grantee_account_id')
        patient_id = self.request.query_params.get('patient_id')
        is_active = self.request.query_params.get('is_active')
        if grantor:
            qs = qs.filter(grantor_account_id=grantor)
        if grantee:
            qs = qs.filter(grantee_account_id=grantee)
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        return qs

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        permission = self.get_object()
        permission.is_active = False
        permission.revoked_at = timezone.now()
        permission.revoked_by = request.user.id
        permission.save(update_fields=['is_active', 'revoked_at', 'revoked_by', 'updated_at'])
        return Response({'status': 'Access permission revoked.'})


class DependentProfileViewSet(viewsets.ModelViewSet):
    serializer_class = DependentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'next_checkup_date']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = DependentProfile.objects.filter(tenant_id=self.request.tenant_id)
        guardian = self.request.query_params.get('guardian_account_id')
        if guardian:
            qs = qs.filter(guardian_account_id=guardian)
        return qs
