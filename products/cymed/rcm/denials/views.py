from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Denial, DenialReason, Appeal, AppealOutcome, CorrectiveAction
from .serializers import (
    DenialSerializer,
    DenialReasonSerializer,
    AppealSerializer,
    AppealOutcomeSerializer,
    CorrectiveActionSerializer,
)


class DenialViewSet(viewsets.ModelViewSet):
    queryset = Denial.objects.all()
    serializer_class = DenialSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "patient_id",
        "insurance_plan_id",
        "denial_category",
        "status",
        "denial_date",
    ]
    search_fields = ["denial_code", "denial_description"]
    ordering_fields = ["denial_date", "denial_amount", "created_at"]
    ordering = ["-denial_date"]

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        denial = self.get_object()
        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"detail": "user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        denial.assigned_to_user_id = user_id
        denial.save(update_fields=["assigned_to_user_id", "updated_at"])
        return Response(DenialSerializer(denial).data)

    @action(detail=True, methods=["post"])
    def write_off(self, request, pk=None):
        denial = self.get_object()
        if denial.status == "written_off":
            return Response(
                {"detail": "Denial is already written off."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        denial.status = "written_off"
        denial.save(update_fields=["status", "updated_at"])
        return Response(DenialSerializer(denial).data)


class DenialReasonViewSet(viewsets.ModelViewSet):
    queryset = DenialReason.objects.all()
    serializer_class = DenialReasonSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "is_active"]
    search_fields = ["denial_code", "description"]
    ordering_fields = ["denial_code", "category"]
    ordering = ["denial_code"]


class AppealViewSet(viewsets.ModelViewSet):
    queryset = Appeal.objects.select_related("denial").all()
    serializer_class = AppealSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["denial", "status", "appeal_level"]
    search_fields = ["appeal_reason", "clinical_justification"]
    ordering_fields = ["appeal_date", "appeal_level", "created_at"]
    ordering = ["-appeal_date"]

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        appeal = self.get_object()
        if appeal.status != "draft":
            return Response(
                {"detail": "Only draft appeals can be submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appeal.status = "submitted"
        appeal.save(update_fields=["status", "updated_at"])
        # Update related denial status
        denial = appeal.denial
        if denial.status != "appealing":
            denial.status = "appealing"
            denial.save(update_fields=["status", "updated_at"])
        return Response(AppealSerializer(appeal).data)


class AppealOutcomeViewSet(viewsets.ModelViewSet):
    queryset = AppealOutcome.objects.select_related("appeal").all()
    serializer_class = AppealOutcomeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["appeal", "outcome"]
    ordering_fields = ["outcome_date", "recovered_amount"]
    ordering = ["-outcome_date"]


class CorrectiveActionViewSet(viewsets.ModelViewSet):
    queryset = CorrectiveAction.objects.select_related("denial").all()
    serializer_class = CorrectiveActionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["denial", "status", "action_type"]
    search_fields = ["description"]
    ordering_fields = ["due_date", "created_at"]
    ordering = ["-created_at"]
