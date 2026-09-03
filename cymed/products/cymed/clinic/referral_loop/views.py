from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import Referral


class ReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = "__all__"
        read_only_fields = ["id", "sent_at", "acknowledged_at",
                             "scheduled_at", "completed_at", "result_shared_at",
                             "created_at", "updated_at"]


class ReferralViewSet(viewsets.ModelViewSet):
    queryset = Referral.objects.all()
    serializer_class = ReferralSerializer

    @action(detail=False, methods=["post"], url_path="send")
    def send(self, request):
        r = services.create_and_send(
            from_tenant_id=request.data["from_tenant_id"],
            to_tenant_id=request.data["to_tenant_id"],
            target_kind=request.data["target_kind"],
            patient_profile_id=request.data["patient_profile_id"],
            reason=request.data["reason"],
            clinical_summary=request.data.get("clinical_summary", ""),
            urgency=request.data.get("urgency", "routine"),
            from_practitioner_id=request.data.get("from_practitioner_id"),
            encounter_id=request.data.get("encounter_id"),
        )
        return Response(ReferralSerializer(r).data, status=201)

    @action(detail=True, methods=["post"], url_path="acknowledge")
    def acknowledge(self, request, pk=None):
        r = services.acknowledge(referral_id=pk,
                                   to_practitioner_id=request.data.get("to_practitioner_id"))
        return Response(ReferralSerializer(r).data)

    @action(detail=True, methods=["post"], url_path="schedule")
    def schedule(self, request, pk=None):
        return Response(ReferralSerializer(services.schedule(referral_id=pk)).data)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        r = services.complete(referral_id=pk, notes=request.data.get("notes", ""))
        return Response(ReferralSerializer(r).data)

    @action(detail=True, methods=["post"], url_path="share-result")
    def share_result(self, request, pk=None):
        r = services.share_result(referral_id=pk,
                                    documents=request.data.get("documents", []))
        return Response(ReferralSerializer(r).data)
