from products.cymed.clinic.billing_bridge.models import (
    ChargeCode,
    ChargeItem,
    ClinicService,
    PriceList,
)
from products.cymed.clinic.billing_bridge.serializers import (
    ChargeCodeSerializer,
    ChargeItemSerializer,
    ClinicServiceSerializer,
    PriceListSerializer,
)
from products.cymed.clinic.views import ClinicModelViewSet


class ChargeCodeViewSet(ClinicModelViewSet):
    queryset = ChargeCode.objects.all()
    serializer_class = ChargeCodeSerializer


class PriceListViewSet(ClinicModelViewSet):
    queryset = PriceList.objects.all()
    serializer_class = PriceListSerializer


class ClinicServiceViewSet(ClinicModelViewSet):
    queryset = ClinicService.objects.all()
    serializer_class = ClinicServiceSerializer


class ChargeItemViewSet(ClinicModelViewSet):
    queryset = ChargeItem.objects.all()
    serializer_class = ChargeItemSerializer
