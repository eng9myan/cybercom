from products.cymed.hospital.views import HospitalModelViewSet
from products.cymed.hospital.maternity.models import Pregnancy, PrenatalEncounter, LaborEpisode, Delivery, NewbornRecord, PostpartumCare
from products.cymed.hospital.maternity.serializers import (
    PregnancySerializer, PrenatalEncounterSerializer, LaborEpisodeSerializer,
    DeliverySerializer, NewbornRecordSerializer, PostpartumCareSerializer
)

class PregnancyViewSet(HospitalModelViewSet):
    queryset = Pregnancy.objects.all()
    serializer_class = PregnancySerializer

class PrenatalEncounterViewSet(HospitalModelViewSet):
    queryset = PrenatalEncounter.objects.all()
    serializer_class = PrenatalEncounterSerializer

class LaborEpisodeViewSet(HospitalModelViewSet):
    queryset = LaborEpisode.objects.all()
    serializer_class = LaborEpisodeSerializer

class DeliveryViewSet(HospitalModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer

class NewbornRecordViewSet(HospitalModelViewSet):
    queryset = NewbornRecord.objects.all()
    serializer_class = NewbornRecordSerializer

class PostpartumCareViewSet(HospitalModelViewSet):
    queryset = PostpartumCare.objects.all()
    serializer_class = PostpartumCareSerializer
