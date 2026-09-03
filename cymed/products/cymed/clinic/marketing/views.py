from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import Campaign, CampaignSend


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = "__all__"


class CampaignSendSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignSend
        fields = "__all__"


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer

    @action(detail=True, methods=["post"], url_path="queue-send")
    def queue_send(self, request, pk=None):
        s = services.queue_send(
            campaign_id=pk,
            patient_profile_id=request.data["patient_profile_id"],
            channel_address=request.data["channel_address"],
            context=request.data.get("context", {}),
        )
        return Response(CampaignSendSerializer(s).data, status=201)


class CampaignSendViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CampaignSend.objects.all()
    serializer_class = CampaignSendSerializer

    @action(detail=True, methods=["post"], url_path="dispatch")
    def dispatch_(self, request, pk=None):
        return Response(CampaignSendSerializer(services.dispatch(send_id=pk)).data)
