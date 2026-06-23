"""CyMed Pharmacy — Formulary Management Views."""
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Formulary, FormularyDrug, FormularyRestriction, TherapeuticClass, PreferredMedication
from .serializers import (
    FormularySerializer, FormularyDrugSerializer, FormularyRestrictionSerializer,
    TherapeuticClassSerializer, PreferredMedicationSerializer
)
from ..views import PharmacyModelViewSet


class TherapeuticClassViewSet(PharmacyModelViewSet):
    queryset = TherapeuticClass.objects.select_related("parent").prefetch_related("children")
    serializer_class = TherapeuticClassSerializer
    required_feature = "pharmacy.formulary"
    filterset_fields = ["level", "is_active"]
    search_fields = ["code", "name", "atc_code"]


class FormularyViewSet(PharmacyModelViewSet):
    queryset = Formulary.objects.prefetch_related("drugs", "preferred_medications")
    serializer_class = FormularySerializer
    required_feature = "pharmacy.formulary"
    filterset_fields = ["formulary_type", "is_active", "is_default"]
    search_fields = ["name"]

    @action(detail=True, methods=["get"], url_path="check-drug")
    def check_drug(self, request, pk=None):
        """Check if a drug is in this formulary."""
        formulary = self.get_object()
        drug_code = request.query_params.get("drug_code", "")
        if not drug_code:
            return Response({"detail": "drug_code query parameter required."}, status=400)
        try:
            entry = formulary.drugs.get(drug_code=drug_code)
            return Response({
                "on_formulary": True,
                "status": entry.status,
                "tier": entry.tier,
                "requires_prior_auth": entry.requires_prior_auth,
            })
        except FormularyDrug.DoesNotExist:
            # Check for preferred alternative
            alternative = formulary.preferred_medications.filter(
                non_formulary_drug_code=drug_code
            ).first()
            return Response({
                "on_formulary": False,
                "preferred_alternative": PreferredMedicationSerializer(alternative).data if alternative else None,
            })


class FormularyDrugViewSet(PharmacyModelViewSet):
    queryset = FormularyDrug.objects.prefetch_related("restrictions").select_related(
        "formulary", "therapeutic_class"
    )
    serializer_class = FormularyDrugSerializer
    required_feature = "pharmacy.formulary"
    filterset_fields = ["formulary", "status", "tier", "requires_prior_auth"]
    search_fields = ["drug_name", "drug_code", "generic_name"]


class FormularyRestrictionViewSet(PharmacyModelViewSet):
    queryset = FormularyRestriction.objects.select_related("formulary_drug")
    serializer_class = FormularyRestrictionSerializer
    required_feature = "pharmacy.formulary"
    filterset_fields = ["restriction_type", "is_hard_stop"]


class PreferredMedicationViewSet(PharmacyModelViewSet):
    queryset = PreferredMedication.objects.select_related("formulary")
    serializer_class = PreferredMedicationSerializer
    required_feature = "pharmacy.formulary"
    filterset_fields = ["formulary", "interchange_reason"]
    search_fields = ["non_formulary_drug_name", "preferred_drug_name"]
