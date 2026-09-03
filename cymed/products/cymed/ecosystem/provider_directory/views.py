"""DRF viewsets and actions for provider directory."""
from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import (
    DirectoryReview,
    NetworkFacility,
    NetworkPractitioner,
    PractitionerFacilityAffiliation,
)
from .serializers import (
    DirectoryReviewSerializer,
    NetworkFacilitySerializer,
    NetworkPractitionerSerializer,
    PractitionerFacilityAffiliationSerializer,
)


class NetworkFacilityViewSet(viewsets.ModelViewSet):
    queryset = NetworkFacility.objects.all()
    serializer_class = NetworkFacilitySerializer

    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request):
        obj = services.register_facility(**request.data)
        return Response(NetworkFacilitySerializer(obj).data)

    @action(detail=False, methods=["post"], url_path="search")
    def search(self, request):
        qs = services.search_facilities(**request.data)
        return Response(NetworkFacilitySerializer(qs, many=True).data)


class NetworkPractitionerViewSet(viewsets.ModelViewSet):
    queryset = NetworkPractitioner.objects.all()
    serializer_class = NetworkPractitionerSerializer

    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request):
        obj = services.register_practitioner(**request.data)
        return Response(NetworkPractitionerSerializer(obj).data)

    @action(detail=False, methods=["post"], url_path="search")
    def search(self, request):
        qs = services.search_practitioners(**request.data)
        return Response(NetworkPractitionerSerializer(qs, many=True).data)

    @action(detail=False, methods=["post"], url_path="affiliate")
    def affiliate(self, request):
        obj = services.affiliate(**request.data)
        return Response(PractitionerFacilityAffiliationSerializer(obj).data)


class PractitionerFacilityAffiliationViewSet(viewsets.ModelViewSet):
    queryset = PractitionerFacilityAffiliation.objects.all()
    serializer_class = PractitionerFacilityAffiliationSerializer


class DirectoryReviewViewSet(viewsets.ModelViewSet):
    queryset = DirectoryReview.objects.all()
    serializer_class = DirectoryReviewSerializer

    @action(detail=False, methods=["post"], url_path="post-review")
    def post_review(self, request):
        obj = services.post_review(**request.data)
        return Response(DirectoryReviewSerializer(obj).data)

    @action(detail=True, methods=["post"], url_path="moderate")
    def moderate(self, request, pk=None):
        payload = dict(request.data)
        payload["review_id"] = pk
        obj = services.moderate_review(**payload)
        return Response(DirectoryReviewSerializer(obj).data)
