"""CyMed Pharmacy — Clinical Pharmacy Views."""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
import django.utils.timezone as tz
from .models import MedicationReview, ClinicalIntervention, PharmacistRecommendation, MedicationTherapyManagement, ReviewStatus
from .serializers import (
    MedicationReviewSerializer, ClinicalInterventionSerializer,
    PharmacistRecommendationSerializer, MedicationTherapyManagementSerializer
)
from ..views import PharmacyModelViewSet


class MedicationReviewViewSet(PharmacyModelViewSet):
    queryset = MedicationReview.objects.prefetch_related("interventions", "recommendations")
    serializer_class = MedicationReviewSerializer
    required_feature = "pharmacy.clinical"
    filterset_fields = ["review_type", "status", "polypharmacy_risk", "patient_id"]

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        """Mark medication review as completed."""
        review = self.get_object()
        review.status = ReviewStatus.COMPLETED
        review.completed_at = tz.now()
        review.save(update_fields=["status", "completed_at", "updated_at"])
        return Response(MedicationReviewSerializer(review).data)

    @action(detail=True, methods=["post"], url_path="ai-analyze")
    def ai_analyze(self, request, pk=None):
        """
        Request CyAI polypharmacy and adherence analysis.
        CyAI provides scoring — pharmacist reviews and acts.
        """
        review = self.get_object()
        try:
            from platform.cyai.services import CyAIService
            score = CyAIService.analyze_polypharmacy(
                medication_codes=review.medications_reviewed,
                patient_age=request.data.get("patient_age"),
                diagnosis_codes=review.diagnoses_considered,
            )
            review.ai_polypharmacy_score = score.get("risk_score", 0.0)
            review.polypharmacy_risk = score.get("risk_level", "low")
            review.adherence_score = score.get("adherence_score")
            review.save(update_fields=["ai_polypharmacy_score", "polypharmacy_risk", "adherence_score"])
        except Exception:
            pass  # CyAI is advisory
        return Response(MedicationReviewSerializer(review).data)


class ClinicalInterventionViewSet(PharmacyModelViewSet):
    queryset = ClinicalIntervention.objects.select_related("review")
    serializer_class = ClinicalInterventionSerializer
    required_feature = "pharmacy.clinical"
    filterset_fields = ["intervention_type", "outcome", "clinical_significance", "patient_id"]


class PharmacistRecommendationViewSet(PharmacyModelViewSet):
    queryset = PharmacistRecommendation.objects.select_related("review")
    serializer_class = PharmacistRecommendationSerializer
    required_feature = "pharmacy.clinical"
    filterset_fields = ["status", "priority", "patient_id"]

    @action(detail=True, methods=["post"], url_path="respond")
    def respond(self, request, pk=None):
        """Record prescriber response to recommendation."""
        rec = self.get_object()
        new_status = request.data.get("status", "accepted")
        rec.status = new_status
        rec.prescriber_response = request.data.get("response", "")
        rec.responded_at = tz.now()
        rec.save(update_fields=["status", "prescriber_response", "responded_at"])
        return Response(PharmacistRecommendationSerializer(rec).data)


class MedicationTherapyManagementViewSet(PharmacyModelViewSet):
    queryset = MedicationTherapyManagement.objects.all()
    serializer_class = MedicationTherapyManagementSerializer
    required_feature = "pharmacy.clinical"
    filterset_fields = ["session_type", "patient_id"]
