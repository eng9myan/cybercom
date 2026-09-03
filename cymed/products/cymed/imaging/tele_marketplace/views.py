"""ViewSets for the teleradiology marketplace API."""

from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import Bid, RadiologistProvider, ReadContract, TeleReadJob, TeleReport
from .serializers import (
    BidSerializer,
    RadiologistProviderSerializer,
    ReadContractSerializer,
    TeleReadJobSerializer,
    TeleReportSerializer,
)


class RadiologistProviderViewSet(viewsets.ModelViewSet):
    queryset = RadiologistProvider.objects.all()
    serializer_class = RadiologistProviderSerializer

    @action(detail=False, methods=["post"], url_path="onboard")
    def onboard(self, request):
        data = request.data
        provider = services.onboard_provider(
            display_name=data.get("display_name"),
            organization=data.get("organization", ""),
            country=data.get("country", ""),
            licenses=data.get("licenses", []),
            modalities=data.get("modalities", []),
            body_parts=data.get("body_parts"),
            subspecialty=data.get("subspecialty"),
            languages=data.get("languages"),
            tier=data.get("tier", "general"),
            hourly_rate=data.get("hourly_rate"),
            per_study_rate=data.get("per_study_rate"),
            tenant_id=data.get("tenant_id"),
        )
        return Response(RadiologistProviderSerializer(provider).data)


class ReadContractViewSet(viewsets.ModelViewSet):
    queryset = ReadContract.objects.all()
    serializer_class = ReadContractSerializer

    @action(detail=False, methods=["post"], url_path="sign")
    def sign(self, request):
        data = request.data
        contract = services.sign_contract(
            tenant_id=data.get("tenant_id"),
            provider_id=data.get("provider_id"),
            start_date=data.get("start_date"),
            payment_terms=data.get("payment_terms"),
            payment_amount=data.get("payment_amount"),
            modalities=data.get("modalities", []),
            nda_signed=data.get("nda_signed", False),
            insurance_verified=data.get("insurance_verified", False),
        )
        return Response(ReadContractSerializer(contract).data)


class TeleReadJobViewSet(viewsets.ModelViewSet):
    queryset = TeleReadJob.objects.all()
    serializer_class = TeleReadJobSerializer

    @action(detail=False, methods=["post"], url_path="post-job")
    def post_job(self, request):
        data = request.data
        job = services.post_job(
            tenant_id=data.get("tenant_id"),
            study_instance_uid=data.get("study_instance_uid"),
            modality=data.get("modality"),
            body_part=data.get("body_part", ""),
            priority=data.get("priority", "routine"),
            patient_profile_id=data.get("patient_profile_id"),
            ordered_by_profile_id=data.get("ordered_by_profile_id"),
            direct_assign_provider_id=data.get("direct_assign_provider_id"),
        )
        return Response(TeleReadJobSerializer(job).data)

    @action(detail=True, methods=["post"], url_path="finalize")
    def finalize(self, request, pk=None):
        job = services.finalize_job(job_id=pk)
        return Response(TeleReadJobSerializer(job).data)

    @action(detail=True, methods=["post"], url_path="dispute")
    def dispute(self, request, pk=None):
        reason = request.data.get("reason", "")
        job = services.dispute_job(job_id=pk, reason=reason)
        return Response(TeleReadJobSerializer(job).data)


class BidViewSet(viewsets.ModelViewSet):
    queryset = Bid.objects.all()
    serializer_class = BidSerializer

    @action(detail=False, methods=["post"], url_path="submit")
    def submit(self, request):
        data = request.data
        bid = services.submit_bid(
            job_id=data.get("job_id"),
            provider_id=data.get("provider_id"),
            amount=data.get("amount"),
            eta_minutes=data.get("eta_minutes"),
            note=data.get("note", ""),
        )
        return Response(BidSerializer(bid).data)

    @action(detail=True, methods=["post"], url_path="accept")
    def accept(self, request, pk=None):
        job = services.accept_bid(bid_id=pk)
        return Response(TeleReadJobSerializer(job).data)


class TeleReportViewSet(viewsets.ModelViewSet):
    queryset = TeleReport.objects.all()
    serializer_class = TeleReportSerializer

    @action(detail=False, methods=["post"], url_path="submit")
    def submit(self, request):
        data = request.data
        report = services.submit_report(
            job_id=data.get("job_id"),
            provider_id=data.get("provider_id"),
            kind=data.get("kind", "preliminary"),
            text=data.get("text", ""),
            findings=data.get("findings"),
            impressions=data.get("impressions", ""),
            signed=data.get("signed", False),
        )
        return Response(TeleReportSerializer(report).data)
