from products.cymed.imaging.views import ImagingModelViewSet

from .models import (
    ImagingOrder,
    ImagingOrderItem,
    ImagingOrderStatusHistory,
    ImagingProcedure,
    ImagingProtocol,
)
from .serializers import (
    ImagingOrderItemSerializer,
    ImagingOrderSerializer,
    ImagingOrderStatusHistorySerializer,
    ImagingProcedureSerializer,
    ImagingProtocolSerializer,
)


class ImagingProtocolViewSet(ImagingModelViewSet):
    queryset = ImagingProtocol.objects.all()
    serializer_class = ImagingProtocolSerializer
    required_feature = "imaging.orders"


class ImagingProcedureViewSet(ImagingModelViewSet):
    queryset = ImagingProcedure.objects.all()
    serializer_class = ImagingProcedureSerializer
    required_feature = "imaging.orders"


class ImagingOrderViewSet(ImagingModelViewSet):
    queryset = ImagingOrder.objects.select_related().prefetch_related("items", "status_history")
    serializer_class = ImagingOrderSerializer
    required_feature = "imaging.orders"


class ImagingOrderItemViewSet(ImagingModelViewSet):
    queryset = ImagingOrderItem.objects.select_related("order", "procedure")
    serializer_class = ImagingOrderItemSerializer
    required_feature = "imaging.orders"


class ImagingOrderStatusHistoryViewSet(ImagingModelViewSet):
    queryset = ImagingOrderStatusHistory.objects.select_related("order")
    serializer_class = ImagingOrderStatusHistorySerializer
    required_feature = "imaging.orders"
    http_method_names = ["get", "head", "options"]
