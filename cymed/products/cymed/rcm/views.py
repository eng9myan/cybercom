from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AppealCase, Claim837, ClaimResponse, DenialCode
from .serializers import (
    AppealCaseSerializer,
    Claim837Serializer,
    ClaimResponseSerializer,
    DenialCodeSerializer,
)
from .services import (
    build_claim_from_bill,
    kpi_snapshot,
    raise_appeal,
    scrub_and_predict,
    submit_claim,
)


class Claim837ViewSet(viewsets.ModelViewSet):
    queryset = Claim837.objects.all()
    serializer_class = Claim837Serializer

    @action(detail=False, methods=["post"], url_path="build")
    def build(self, request):
        claim = build_claim_from_bill(
            bill_id=request.data["bill_id"],
            encounter_id=request.data["encounter_id"],
            payer_code=request.data["payer_code"],
            payer_country=request.data.get("payer_country", "SA"),
            kind=request.data.get("kind", "professional"),
        )
        return Response(Claim837Serializer(claim).data, status=201)

    @action(detail=True, methods=["post"], url_path="scrub")
    def scrub(self, request, pk=None):
        return Response(scrub_and_predict(claim_id=pk))

    @action(detail=True, methods=["post"], url_path="predict-denial")
    def predict_denial(self, request, pk=None):
        from .engines import ClaimScrubber, DenialPredictor
        claim = self.get_object()
        errors = ClaimScrubber().scrub(claim)
        return Response(DenialPredictor().predict(claim, scrub_errors=errors))

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        result = submit_claim(claim_id=pk)
        if isinstance(result, ClaimResponse):
            return Response(ClaimResponseSerializer(result).data, status=201)
        return Response(result, status=400)

    @action(detail=True, methods=["post"], url_path="appeal")
    def appeal(self, request, pk=None):
        appeal = raise_appeal(
            claim_id=pk,
            narrative=request.data.get("narrative", ""),
            denial_codes=request.data.get("denial_codes"),
            level=int(request.data.get("level", 1)),
        )
        return Response(AppealCaseSerializer(appeal).data, status=201)


class ClaimResponseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ClaimResponse.objects.all()
    serializer_class = ClaimResponseSerializer


class AppealCaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AppealCase.objects.all()
    serializer_class = AppealCaseSerializer


class DenialCodeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DenialCode.objects.all()
    serializer_class = DenialCodeSerializer


class DenialsListView(APIView):
    def get(self, request):
        qs = Claim837.objects.filter(status="denied").order_by("-denied_at")[:200]
        return Response(Claim837Serializer(qs, many=True).data)


class KPIView(APIView):
    def get(self, request):
        return Response(kpi_snapshot())
