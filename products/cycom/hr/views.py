from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Department, Employee, Attendance, LeaveRequest, PerformanceReview
from .serializers import (
    DepartmentSerializer,
    EmployeeSerializer,
    AttendanceSerializer,
    LeaveRequestSerializer,
    PerformanceReviewSerializer,
)


class BaseHRViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        return self.queryset.filter(tenant_id=tenant_id)

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        serializer.save(tenant_id=tenant_id)


class DepartmentViewSet(BaseHRViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class EmployeeViewSet(BaseHRViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


class AttendanceViewSet(BaseHRViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer


class LeaveRequestViewSet(BaseHRViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer


class PerformanceReviewViewSet(BaseHRViewSet):
    queryset = PerformanceReview.objects.all()
    serializer_class = PerformanceReviewSerializer
