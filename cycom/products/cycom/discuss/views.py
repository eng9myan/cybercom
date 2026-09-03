from core.viewsets import TenantScopedModelViewSet
from products.cycom.discuss.models import Channel, Message
from products.cycom.discuss.serializers import ChannelSerializer, MessageSerializer


class ChannelViewSet(TenantScopedModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer


class MessageViewSet(TenantScopedModelViewSet):
    queryset = Message.objects.select_related("channel").all()
    serializer_class = MessageSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        channel_id = self.request.query_params.get("channel")
        if channel_id:
            qs = qs.filter(channel_id=channel_id)
        return qs
