from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import Employee, Contract, LeaveType, LeaveRequest
from .serializers import (
    EmployeeSerializer, ContractSerializer,
    LeaveTypeSerializer, LeaveRequestSerializer,
)


class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        qs = Employee.objects.filter(tenant_id=self.request.tenant_id)
        department = self.request.query_params.get('department')
        if department:
            qs = qs.filter(department=department)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        branch = self.request.query_params.get('branch')
        if branch:
            qs = qs.filter(branch=branch)
        return qs.select_related('department', 'branch', 'user')


class ContractViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ContractSerializer

    def get_queryset(self):
        qs = Contract.objects.filter(employee__tenant_id=self.request.tenant_id)
        employee = self.request.query_params.get('employee')
        if employee:
            qs = qs.filter(employee=employee)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('1', 'true'))
        return qs.select_related('employee')


class LeaveTypeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = LeaveTypeSerializer

    def get_queryset(self):
        return LeaveType.objects.filter(tenant_id=self.request.tenant_id)


class LeaveRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = LeaveRequestSerializer

    def get_queryset(self):
        qs = LeaveRequest.objects.filter(employee__tenant_id=self.request.tenant_id)
        employee = self.request.query_params.get('employee')
        if employee:
            qs = qs.filter(employee=employee)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.select_related('employee', 'leave_type', 'approved_by')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        leave_request = self.get_object()
        leave_request.status = 'approved'
        leave_request.approved_by = request.user
        leave_request.approved_at = timezone.now()
        leave_request.save()
        return Response(
            LeaveRequestSerializer(leave_request, context={'request': request}).data
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        leave_request = self.get_object()
        leave_request.status = 'rejected'
        leave_request.approved_by = request.user
        leave_request.approved_at = timezone.now()
        leave_request.save()
        return Response(
            LeaveRequestSerializer(leave_request, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )
