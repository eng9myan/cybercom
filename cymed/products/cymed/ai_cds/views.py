from decimal import Decimal

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .engines import (
    FallRiskEngine,
    ICDNLPEngine,
    InteractionEngine,
    NEWS2Engine,
    ReadmissionEngine,
    SepsisEngine,
)
from .engines.interactions import DrugContext, PatientContext
from .engines.risk_scores import Vitals
from .models import CDSAlert, ICDCodeSuggestion, RiskScore
from .serializers import (
    CDSAlertSerializer,
    ICDCodeSuggestionSerializer,
    RiskScoreSerializer,
)


class CDSAlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CDSAlert.objects.all()
    serializer_class = CDSAlertSerializer

    @action(detail=True, methods=["post"], url_path="acknowledge")
    def acknowledge(self, request, pk=None):
        from django.utils import timezone
        alert = self.get_object()
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = request.user.id if request.user.is_authenticated else None
        alert.overridden = bool(request.data.get("override", False))
        alert.override_reason = request.data.get("reason", "")
        alert.save(update_fields=["acknowledged_at", "acknowledged_by",
                                    "overridden", "override_reason", "updated_at"])
        return Response({"status": "acknowledged"})


class RiskScoreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RiskScore.objects.all()
    serializer_class = RiskScoreSerializer


class ICDSuggestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ICDCodeSuggestion.objects.all()
    serializer_class = ICDCodeSuggestionSerializer


# ── One-shot compute endpoints ────────────────────────────────────────
class InteractionCheckView(APIView):
    def post(self, request):
        p = request.data.get("patient", {})
        drugs = request.data.get("drugs", [])
        patient = PatientContext(
            id=p["id"],
            weight_kg=_dec(p.get("weight_kg")),
            age_years=_dec(p.get("age_years")),
            pregnancy_weeks=p.get("pregnancy_weeks"),
            egfr_ml_min=_dec(p.get("egfr_ml_min")),
            allergies=p.get("allergies", []),
            active_meds=[DrugContext(**m) for m in p.get("active_meds", [])],
        )
        new_drugs = [DrugContext(rxnorm=d.get("rxnorm", ""), name=d["name"],
                                  dose_mg=_dec(d.get("dose_mg")),
                                  route=d.get("route", ""),
                                  frequency=d.get("frequency", ""))
                     for d in drugs]
        alerts = InteractionEngine().check(patient, new_drugs)
        return Response({"alerts": alerts})


class NEWS2View(APIView):
    def post(self, request):
        v = Vitals(**{k: request.data.get(k) for k in
                     ["hr", "sbp", "rr", "temp_c", "spo2",
                      "o2_supplement", "consciousness", "gcs", "wbc"] if k in request.data})
        return Response(NEWS2Engine().compute(
            patient_id=request.data["patient_id"],
            encounter_id=request.data.get("encounter_id"),
            v=v,
        ))


class SepsisView(APIView):
    def post(self, request):
        v = Vitals(**{k: request.data.get(k) for k in
                     ["hr", "sbp", "rr", "temp_c", "spo2",
                      "consciousness", "gcs", "wbc", "lactate"] if k in request.data})
        return Response(SepsisEngine().compute(
            patient_id=request.data["patient_id"],
            encounter_id=request.data.get("encounter_id"),
            v=v,
            suspected_infection=bool(request.data.get("suspected_infection", False)),
        ))


class ReadmissionView(APIView):
    def post(self, request):
        return Response(ReadmissionEngine().compute(
            patient_id=request.data["patient_id"],
            encounter_id=request.data.get("encounter_id"),
            los_days=int(request.data.get("los_days", 0)),
            emergency_admission=bool(request.data.get("emergency_admission", False)),
            charlson_index=int(request.data.get("charlson_index", 0)),
            ed_visits_last_6mo=int(request.data.get("ed_visits_last_6mo", 0)),
        ))


class FallRiskView(APIView):
    def post(self, request):
        return Response(FallRiskEngine().compute(
            patient_id=request.data["patient_id"],
            encounter_id=request.data.get("encounter_id"),
            history_of_fall=bool(request.data.get("history_of_fall", False)),
            secondary_diagnosis=bool(request.data.get("secondary_diagnosis", False)),
            ambulatory_aid=request.data.get("ambulatory_aid", "none"),
            iv_therapy=bool(request.data.get("iv_therapy", False)),
            gait=request.data.get("gait", "normal"),
            mental_status_impaired=bool(request.data.get("mental_status_impaired", False)),
        ))


class ICDSuggestView(APIView):
    def post(self, request):
        return Response(ICDNLPEngine().suggest(
            encounter_id=request.data["encounter_id"],
            source_text=request.data.get("text", ""),
            limit=int(request.data.get("limit", 5)),
        ))


def _dec(x):
    return Decimal(str(x)) if x is not None else None
