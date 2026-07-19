from core.viewsets import TenantScopedModelViewSet
from products.cycom.scheduler.models import Event
from products.cycom.scheduler.serializers import EventSerializer


class EventViewSet(TenantScopedModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        after = self.request.query_params.get("after")
        before = self.request.query_params.get("before")
        if after:
            qs = qs.filter(start_at__gte=after)
        if before:
            qs = qs.filter(start_at__lte=before)
        return qs
