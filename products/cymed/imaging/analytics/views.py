from products.cymed.imaging.views import ImagingModelViewSet
from .models import ImagingOperationsDashboard, RadiologistProductivity, TeleradiologyDashboard, ImagingRevenueEvent
from .serializers import (
    ImagingOperationsDashboardSerializer, RadiologistProductivitySerializer,
    TeleradiologyDashboardSerializer, ImagingRevenueEventSerializer,
)


class ImagingOperationsDashboardViewSet(ImagingModelViewSet):
    queryset = ImagingOperationsDashboard.objects.all()
    serializer_class = ImagingOperationsDashboardSerializer
    required_feature = "imaging.analytics"
    http_method_names = ["get", "head", "options"]


class RadiologistProductivityViewSet(ImagingModelViewSet):
    queryset = RadiologistProductivity.objects.all()
    serializer_class = RadiologistProductivitySerializer
    required_feature = "imaging.analytics"
    http_method_names = ["get", "head", "options"]


class TeleradiologyDashboardViewSet(ImagingModelViewSet):
    queryset = TeleradiologyDashboard.objects.all()
    serializer_class = TeleradiologyDashboardSerializer
    required_feature = "imaging.analytics"
    http_method_names = ["get", "head", "options"]


class ImagingRevenueEventViewSet(ImagingModelViewSet):
    queryset = ImagingRevenueEvent.objects.all()
    serializer_class = ImagingRevenueEventSerializer
    required_feature = "imaging.analytics"
    http_method_names = ["get", "head", "options"]
