from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    CareTeam,
    CareTeamMember,
    CareTeamAssignment,
    CareTeamRole,
    CoverageSchedule,
)
from .serializers import (
    CareTeamSerializer,
    CareTeamMemberSerializer,
    CareTeamAssignmentSerializer,
    CareTeamRoleSerializer,
    CoverageScheduleSerializer,
)


class CareTeamViewSet(viewsets.ModelViewSet):
    serializer_class = CareTeamSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['team_type', 'patient_id', 'unit_id', 'specialty', 'is_active', 'created_by_provider_id']
    search_fields = ['team_name', 'specialty', 'description']
    ordering_fields = ['created_at', 'team_name', 'team_type']
    ordering = ['-created_at']

    def get_queryset(self):
        return CareTeam.objects.filter(
            tenant_id=self.request.tenant_id
        ).prefetch_related('members', 'patient_assignments', 'coverage_schedules')


class CareTeamMemberViewSet(viewsets.ModelViewSet):
    serializer_class = CareTeamMemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['care_team', 'provider_id', 'role', 'is_primary', 'is_active']
    search_fields = ['provider_name', 'provider_type', 'role']
    ordering_fields = ['created_at', 'joined_at', 'role', 'provider_name']
    ordering = ['-joined_at']

    def get_queryset(self):
        return CareTeamMember.objects.filter(tenant_id=self.request.tenant_id)


class CareTeamAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = CareTeamAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['care_team', 'patient_id', 'cymed_encounter_id', 'is_active']
    search_fields = ['assignment_reason']
    ordering_fields = ['created_at', 'assigned_at', 'unassigned_at']
    ordering = ['-assigned_at']

    def get_queryset(self):
        return CareTeamAssignment.objects.filter(tenant_id=self.request.tenant_id)


class CareTeamRoleViewSet(viewsets.ModelViewSet):
    serializer_class = CareTeamRoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role_type', 'can_order', 'can_sign_documents', 'is_active']
    search_fields = ['role_code', 'role_name', 'role_type']
    ordering_fields = ['created_at', 'role_name', 'role_type']
    ordering = ['role_name']

    def get_queryset(self):
        return CareTeamRole.objects.filter(tenant_id=self.request.tenant_id)


class CoverageScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = CoverageScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'care_team', 'covering_provider_id', 'covered_provider_id',
        'coverage_date', 'coverage_type', 'is_active',
    ]
    search_fields = ['covering_provider_name', 'coverage_type']
    ordering_fields = ['created_at', 'coverage_date', 'coverage_start', 'coverage_type']
    ordering = ['coverage_date', 'coverage_start']

    def get_queryset(self):
        return CoverageSchedule.objects.filter(tenant_id=self.request.tenant_id)
