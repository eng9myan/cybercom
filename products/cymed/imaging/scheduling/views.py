from products.cymed.imaging.views import ImagingModelViewSet
from .models import ImagingRoom, ImagingAppointment, ModalitySchedule, RadiologistSchedule
from .serializers import (
    ImagingRoomSerializer, ImagingAppointmentSerializer,
    ModalityScheduleSerializer, RadiologistScheduleSerializer,
)


class ImagingRoomViewSet(ImagingModelViewSet):
    queryset = ImagingRoom.objects.all()
    serializer_class = ImagingRoomSerializer
    required_feature = "imaging.scheduling"


class ImagingAppointmentViewSet(ImagingModelViewSet):
    queryset = ImagingAppointment.objects.select_related("modality", "room")
    serializer_class = ImagingAppointmentSerializer
    required_feature = "imaging.scheduling"


class ModalityScheduleViewSet(ImagingModelViewSet):
    queryset = ModalitySchedule.objects.select_related("modality")
    serializer_class = ModalityScheduleSerializer
    required_feature = "imaging.scheduling"


class RadiologistScheduleViewSet(ImagingModelViewSet):
    queryset = RadiologistSchedule.objects.all()
    serializer_class = RadiologistScheduleSerializer
    required_feature = "imaging.scheduling"
