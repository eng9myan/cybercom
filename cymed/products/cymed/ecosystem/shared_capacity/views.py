"""DRF views for CyMed shared capacity marketplace and pools."""
from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import (
    RadiologistPoolShift,
    ResourceMatch,
    ResourceOffer,
    ResourceRequest,
)
from .serializers import (
    RadiologistPoolShiftSerializer,
    ResourceMatchSerializer,
    ResourceOfferSerializer,
    ResourceRequestSerializer,
)


class ResourceOfferViewSet(viewsets.ModelViewSet):
    queryset = ResourceOffer.objects.all()
    serializer_class = ResourceOfferSerializer

    @action(detail=False, methods=["post"], url_path="post-offer")
    def post_offer(self, request):
        data = request.data
        offer = services.post_offer(
            tenant_id=data.get("tenant_id"),
            kind=data.get("kind"),
            quantity=data.get("quantity", 0),
            uom=data.get("uom", ""),
            code=data.get("code", ""),
            description=data.get("description", ""),
            start_at=data.get("start_at"),
            end_at=data.get("end_at"),
            location=data.get("location"),
            price_per_unit=data.get("price_per_unit"),
            currency=data.get("currency", "SAR"),
            tags=data.get("tags"),
            visible_to_tenant_ids=data.get("visible_to_tenant_ids"),
        )
        return Response(ResourceOfferSerializer(offer).data)


class ResourceRequestViewSet(viewsets.ModelViewSet):
    queryset = ResourceRequest.objects.all()
    serializer_class = ResourceRequestSerializer

    @action(detail=False, methods=["post"], url_path="post-request")
    def post_request(self, request):
        data = request.data
        req = services.post_request(
            tenant_id=data.get("tenant_id"),
            kind=data.get("kind"),
            quantity_needed=data.get("quantity_needed", 0),
            uom=data.get("uom", ""),
            code=data.get("code", ""),
            description=data.get("description", ""),
            needed_by=data.get("needed_by"),
            max_price_per_unit=data.get("max_price_per_unit"),
            currency=data.get("currency", "SAR"),
            location=data.get("location"),
            urgency=data.get("urgency", "routine"),
        )
        return Response(ResourceRequestSerializer(req).data)

    @action(detail=True, methods=["post"], url_path="match")
    def match(self, request, pk=None):
        matches = services.match_request(request_id=pk)
        return Response(ResourceMatchSerializer(matches, many=True).data)


class ResourceMatchViewSet(viewsets.ModelViewSet):
    queryset = ResourceMatch.objects.all()
    serializer_class = ResourceMatchSerializer

    @action(detail=True, methods=["post"], url_path="accept")
    def accept(self, request, pk=None):
        match = services.accept_match(match_id=pk)
        return Response(ResourceMatchSerializer(match).data)

    @action(detail=True, methods=["post"], url_path="decline")
    def decline(self, request, pk=None):
        reason = request.data.get("reason", "")
        match = services.decline_match(match_id=pk, reason=reason)
        return Response(ResourceMatchSerializer(match).data)

    @action(detail=True, methods=["post"], url_path="fulfill")
    def fulfill(self, request, pk=None):
        match = services.fulfill_match(match_id=pk)
        return Response(ResourceMatchSerializer(match).data)


class RadiologistPoolShiftViewSet(viewsets.ModelViewSet):
    queryset = RadiologistPoolShift.objects.all()
    serializer_class = RadiologistPoolShiftSerializer

    @action(detail=False, methods=["post"], url_path="post-shift")
    def post_shift(self, request):
        data = request.data
        shift = services.post_radiologist_shift(
            tenant_id=data.get("tenant_id"),
            provider_id=data.get("provider_id"),
            date=data.get("date"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            modalities=data.get("modalities", []),
            max_studies=data.get("max_studies", 0),
        )
        return Response(RadiologistPoolShiftSerializer(shift).data)

    @action(detail=True, methods=["post"], url_path="increment-load")
    def increment_load(self, request, pk=None):
        n = int(request.data.get("n", 1))
        shift = services.increment_shift_load(shift_id=pk, n=n)
        return Response(RadiologistPoolShiftSerializer(shift).data)
