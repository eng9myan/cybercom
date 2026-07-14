from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .models import (
    Charge,
    ChargeAdjustment,
    ChargeAudit,
    ChargeItem,
    ChargeRule,
)
from .serializers import (
    ChargeAdjustmentSerializer,
    ChargeAuditSerializer,
    ChargeItemSerializer,
    ChargeRuleSerializer,
    ChargeSerializer,
    ChargeWriteSerializer,
)


class ChargeViewSet(ModelViewSet):
    """
    CRUD for charges with `approve` and `void` actions.
    Supports filtering by patient_id, encounter_id, service_source, charge_category,
    status, and charge_date.
    """

    queryset = Charge.objects.all().order_by("-charge_date")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "patient_id",
        "encounter_id",
        "service_source",
        "charge_category",
        "status",
        "charge_date",
    ]
    search_fields = ["service_code", "service_description", "icd11_diagnosis_code"]
    ordering_fields = ["charge_date", "created_at", "total_amount", "status"]
    ordering = ["-charge_date"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ChargeWriteSerializer
        return ChargeSerializer

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """
        Approve a pending or reviewed charge for billing.
        Transitions status to 'approved' and creates an audit entry.
        """
        charge = self.get_object()

        if charge.status not in ("pending", "reviewed"):
            return Response(
                {
                    "detail": (
                        f"Cannot approve a charge with status '{charge.status}'. "
                        "Only 'pending' or 'reviewed' charges can be approved."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        previous_status = charge.status
        charge.status = "approved"
        charge.save(update_fields=["status", "updated_at"])

        ChargeAudit.objects.create(
            tenant_id=charge.tenant_id,
            charge=charge,
            action="approved",
            performed_by_user_id=request.user.id
            if request.user.is_authenticated
            else None or charge.tenant_id,
            previous_status=previous_status,
            new_status="approved",
        )

        serializer = ChargeSerializer(charge, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="void")
    def void(self, request, pk=None):
        """
        Void a charge that has not yet been billed.
        Transitions status to 'voided' and creates an audit entry.
        """
        charge = self.get_object()

        if charge.status == "billed":
            return Response(
                {
                    "detail": "Cannot void a charge that has already been billed. "
                    "Use a billing adjustment or reversal instead."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if charge.status == "voided":
            return Response(
                {"detail": "Charge is already voided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        previous_status = charge.status
        charge.status = "voided"
        charge.save(update_fields=["status", "updated_at"])

        ChargeAudit.objects.create(
            tenant_id=charge.tenant_id,
            charge=charge,
            action="voided",
            performed_by_user_id=request.user.id
            if request.user.is_authenticated
            else None or charge.tenant_id,
            previous_status=previous_status,
            new_status="voided",
            notes=request.data.get("notes", ""),
        )

        serializer = ChargeSerializer(charge, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChargeItemViewSet(ModelViewSet):
    """
    CRUD for charge line items.
    Supports filtering by charge.
    """

    queryset = ChargeItem.objects.all().order_by("created_at")
    serializer_class = ChargeItemSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["charge"]
    search_fields = ["item_code", "item_description"]
    ordering_fields = ["created_at", "total_cost"]
    ordering = ["created_at"]


class ChargeRuleViewSet(ModelViewSet):
    """
    CRUD for charge automation rules.
    Supports filtering by service_source and is_active.
    """

    queryset = ChargeRule.objects.all().order_by("rule_name")
    serializer_class = ChargeRuleSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["service_source", "is_active"]
    search_fields = ["rule_name", "trigger_event"]
    ordering_fields = ["rule_name", "service_source", "is_active"]
    ordering = ["rule_name"]


class ChargeAdjustmentViewSet(ModelViewSet):
    """
    CRUD for charge adjustments.
    Supports filtering by charge and adjustment_type.
    """

    queryset = ChargeAdjustment.objects.all().order_by("-created_at")
    serializer_class = ChargeAdjustmentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["charge", "adjustment_type"]
    search_fields = ["reason"]
    ordering_fields = ["created_at", "adjusted_amount", "adjustment_type"]
    ordering = ["-created_at"]


class ChargeAuditViewSet(ReadOnlyModelViewSet):
    """
    Read-only audit trail for charges.
    Supports filtering by charge.
    """

    queryset = ChargeAudit.objects.all().order_by("-created_at")
    serializer_class = ChargeAuditSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["charge"]
    search_fields = ["notes", "action"]
    ordering_fields = ["created_at", "action"]
    ordering = ["-created_at"]
