"""CyMed Pharmacy — Drug Interaction Views."""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from platform.events.models import OutboxEvent
from .models import InteractionRule, DrugInteraction, InteractionSeverity, InteractionAlert
from .serializers import (
    InteractionRuleSerializer, DrugInteractionSerializer, InteractionSeveritySerializer,
    InteractionAlertSerializer, InteractionCheckSerializer, InteractionOverrideSerializer
)
from .services import DrugInteractionService
from ..views import PharmacyModelViewSet


class InteractionRuleViewSet(PharmacyModelViewSet):
    queryset = InteractionRule.objects.all()
    serializer_class = InteractionRuleSerializer
    required_feature = "pharmacy.interactions"
    filterset_fields = ["interaction_type", "severity", "is_active", "override_allowed"]
    search_fields = ["rule_code", "drug_a_name", "drug_b_name", "drug_a_code", "drug_b_code"]


class DrugInteractionViewSet(PharmacyModelViewSet):
    queryset = DrugInteraction.objects.prefetch_related("alerts").select_related("rule")
    serializer_class = DrugInteractionSerializer
    required_feature = "pharmacy.interactions"
    filterset_fields = ["interaction_type", "severity", "alert_status", "patient_id"]
    search_fields = ["drug_a_name", "drug_b_name"]

    @action(detail=False, methods=["post"], url_path="check")
    def check(self, request):
        """
        Run interaction check for a set of drugs.
        AI may assist with prioritization; pharmacist makes all decisions.
        """
        serializer = InteractionCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        tenant_id = getattr(request, "tenant_id", None)

        interactions = DrugInteractionService.check_prescription(
            patient_id=data["patient_id"],
            drug_codes=data["drug_codes"],
            prescription_id=data.get("prescription_id"),
            encounter_id=data.get("encounter_id"),
            patient_allergies=data.get("patient_allergies", []),
            patient_diagnoses=data.get("patient_diagnoses", []),
            patient_age_years=data.get("patient_age_years"),
            is_pregnant=data.get("is_pregnant", False),
            pregnancy_trimester=data.get("pregnancy_trimester", ""),
            tenant_id=tenant_id,
        )

        if interactions:
            OutboxEvent.objects.create(
                tenant_id=str(tenant_id) if tenant_id else None,
                topic="cymed.pharmacy.interaction.detected",
                event_type="cymed.pharmacy.interaction.detected",
                payload={
                    "patient_id": str(data["patient_id"]),
                    "interaction_count": len(interactions),
                    "severity_summary": {
                        i.severity: sum(1 for x in interactions if x.severity == i.severity)
                        for i in interactions
                    },
                },
            )

        return Response({
            "interaction_count": len(interactions),
            "interactions": DrugInteractionSerializer(interactions, many=True).data,
        })

    @action(detail=True, methods=["post"], url_path="override")
    def override(self, request, pk=None):
        """
        Pharmacist override of an interaction with justification.
        AI cannot approve — pharmacist approval required.
        """
        interaction = self.get_object()
        serializer = InteractionOverrideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pharmacist_id = request.user.id if hasattr(request, "user") else None
        if pharmacist_id is None:
            return Response({"detail": "Pharmacist authentication required."}, status=status.HTTP_403_FORBIDDEN)

        try:
            updated = DrugInteractionService.override_interaction(
                interaction_id=interaction.id,
                pharmacist_id=pharmacist_id,
                override_reason=serializer.validated_data["override_reason"],
                tenant_id=getattr(request, "tenant_id", None),
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(DrugInteractionSerializer(updated).data)


class InteractionSeverityViewSet(PharmacyModelViewSet):
    queryset = InteractionSeverity.objects.all()
    serializer_class = InteractionSeveritySerializer
    required_feature = "pharmacy.interactions"


class InteractionAlertViewSet(PharmacyModelViewSet):
    queryset = InteractionAlert.objects.select_related("interaction")
    serializer_class = InteractionAlertSerializer
    required_feature = "pharmacy.interactions"
    filterset_fields = ["channel", "recipient_id"]
