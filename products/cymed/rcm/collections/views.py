from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import CollectionCase, CollectionAction, PaymentPlan, CollectionOutcome
from .serializers import (
    CollectionCaseSerializer,
    CollectionActionSerializer,
    PaymentPlanSerializer,
    CollectionOutcomeSerializer,
)


class CollectionCaseViewSet(viewsets.ModelViewSet):
    queryset = CollectionCase.objects.all()
    serializer_class = CollectionCaseSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["patient_id", "aging_bucket", "status", "priority"]
    search_fields = ["case_number", "notes"]
    ordering_fields = [
        "outstanding_balance",
        "original_balance",
        "next_follow_up_date",
        "created_at",
    ]
    ordering = ["-created_at"]

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        case = self.get_object()
        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"detail": "user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        case.assigned_to_user_id = user_id
        case.save(update_fields=["assigned_to_user_id", "updated_at"])
        return Response(CollectionCaseSerializer(case).data)

    @action(detail=True, methods=["post"])
    def write_off(self, request, pk=None):
        case = self.get_object()
        if case.status == "written_off":
            return Response(
                {"detail": "Case is already written off."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        case.status = "written_off"
        case.save(update_fields=["status", "updated_at"])
        return Response(CollectionCaseSerializer(case).data)


class CollectionActionViewSet(viewsets.ModelViewSet):
    queryset = CollectionAction.objects.select_related("collection_case").all()
    serializer_class = CollectionActionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["collection_case", "action_type"]
    search_fields = ["notes"]
    ordering_fields = ["action_date", "amount_collected"]
    ordering = ["-action_date"]


class PaymentPlanViewSet(viewsets.ModelViewSet):
    queryset = PaymentPlan.objects.select_related("collection_case").all()
    serializer_class = PaymentPlanSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["collection_case", "status", "frequency"]
    ordering_fields = ["start_date", "end_date", "total_amount", "created_at"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        plan = self.get_object()
        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"detail": "user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if plan.status != "active":
            return Response(
                {"detail": "Only active payment plans can be approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        plan.approved_by_user_id = user_id
        plan.save(update_fields=["approved_by_user_id", "updated_at"])
        # Reflect on the case
        case = plan.collection_case
        if case.status == "active":
            case.status = "payment_plan"
            case.save(update_fields=["status", "updated_at"])
        return Response(PaymentPlanSerializer(plan).data)


class CollectionOutcomeViewSet(viewsets.ModelViewSet):
    queryset = CollectionOutcome.objects.select_related("collection_case").all()
    serializer_class = CollectionOutcomeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["collection_case", "outcome_type"]
    ordering_fields = ["outcome_date", "amount_recovered", "amount_written_off"]
    ordering = ["-outcome_date"]
