from platform.events.models import OutboxEvent
from .models import Specimen, SpecimenContainer, SpecimenCollection, SpecimenTransport, SpecimenStorage, SpecimenRejection, SpecimenChainOfCustody
from .serializers import SpecimenSerializer, SpecimenContainerSerializer, SpecimenCollectionSerializer, SpecimenTransportSerializer, SpecimenStorageSerializer, SpecimenRejectionSerializer, SpecimenChainOfCustodySerializer
from ..views import LaboratoryModelViewSet

class SpecimenViewSet(LaboratoryModelViewSet):
    queryset = Specimen.objects.all()
    serializer_class = SpecimenSerializer
    required_feature = "lab.specimens"
    filterset_fields = ["specimen_type", "status", "patient_id"]
    search_fields = ["specimen_number", "barcode"]

    def perform_create(self, serializer):
        import uuid
        tenant_id = getattr(self.request, "tenant_id", None)
        obj = serializer.save(tenant_id=tenant_id, specimen_number=f"SP-{str(uuid.uuid4()).upper()[:10]}")
        OutboxEvent.objects.create(
            tenant_id=str(tenant_id) if tenant_id else None,
            topic="cymed.lab.specimen.collected",
            event_type="cymed.lab.specimen.collected",
            payload={"specimen_id": str(obj.id), "specimen_number": obj.specimen_number, "type": obj.specimen_type},
        )

class SpecimenContainerViewSet(LaboratoryModelViewSet):
    queryset = SpecimenContainer.objects.all()
    serializer_class = SpecimenContainerSerializer
    required_feature = "lab.specimens"

class SpecimenCollectionViewSet(LaboratoryModelViewSet):
    queryset = SpecimenCollection.objects.all()
    serializer_class = SpecimenCollectionSerializer
    required_feature = "lab.specimens"

class SpecimenTransportViewSet(LaboratoryModelViewSet):
    queryset = SpecimenTransport.objects.all()
    serializer_class = SpecimenTransportSerializer
    required_feature = "lab.specimens"

class SpecimenStorageViewSet(LaboratoryModelViewSet):
    queryset = SpecimenStorage.objects.all()
    serializer_class = SpecimenStorageSerializer
    required_feature = "lab.specimens"

class SpecimenRejectionViewSet(LaboratoryModelViewSet):
    queryset = SpecimenRejection.objects.all()
    serializer_class = SpecimenRejectionSerializer
    required_feature = "lab.specimens"

    def perform_create(self, serializer):
        from django.utils import timezone
        tenant_id = getattr(self.request, "tenant_id", None)
        obj = serializer.save(tenant_id=tenant_id)
        specimen = obj.specimen
        specimen.status = "rejected"
        specimen.save(update_fields=["status", "updated_at"])
        OutboxEvent.objects.create(
            tenant_id=str(tenant_id) if tenant_id else None,
            topic="cymed.lab.specimen.rejected",
            event_type="cymed.lab.specimen.rejected",
            payload={"specimen_id": str(specimen.id), "reason": obj.rejection_reason},
        )

class SpecimenChainOfCustodyViewSet(LaboratoryModelViewSet):
    queryset = SpecimenChainOfCustody.objects.all()
    serializer_class = SpecimenChainOfCustodySerializer
    required_feature = "lab.specimens"
