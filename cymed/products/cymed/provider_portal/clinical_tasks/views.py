from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from products.cymed.provider_portal.clinical_tasks.models import (
    ClinicalTask,
    TaskAssignment,
    TaskComment,
    TaskEscalation,
)
from products.cymed.provider_portal.clinical_tasks.serializers import (
    ClinicalTaskSerializer,
    TaskAssignmentSerializer,
    TaskCommentSerializer,
    TaskEscalationSerializer,
)


class ClinicalTaskViewSet(viewsets.ModelViewSet):
    queryset = ClinicalTask.objects.all()
    serializer_class = ClinicalTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "task_type",
        "priority",
        "status",
        "assigned_to_provider_id",
        "patient_id",
        "unit_id",
    ]
    search_fields = ["title", "description", "notes"]
    ordering_fields = ["created_at", "due_at", "priority", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)


class TaskAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TaskAssignment.objects.all()
    serializer_class = TaskAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["task", "provider_id", "assignment_type", "is_active"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)


class TaskCommentViewSet(viewsets.ModelViewSet):
    queryset = TaskComment.objects.all()
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["task", "author_provider_id", "is_system_comment"]
    search_fields = ["comment_text", "author_name"]
    ordering_fields = ["created_at"]
    ordering = ["created_at"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)


class TaskEscalationViewSet(viewsets.ModelViewSet):
    queryset = TaskEscalation.objects.all()
    serializer_class = TaskEscalationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = [
        "task",
        "escalated_by_provider_id",
        "escalated_to_provider_id",
        "new_priority",
    ]
    ordering_fields = ["created_at", "acknowledged_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)
