from platform.canonical import events as canonical_events

from ..views import LaboratoryModelViewSet
from .models import (
    Specimen,
    SpecimenChainOfCustody,
    SpecimenCollection,
    SpecimenContainer,
    SpecimenRejection,
    SpecimenStorage,
    SpecimenTransport,
)
from .serializers import (
    SpecimenChainOfCustodySerializer,
    SpecimenCollectionSerializer,
    SpecimenContainerSerializer,
    SpecimenRejectionSerializer,
    SpecimenSerializer,
    SpecimenStorageSerializer,
    SpecimenTransportSerializer,
)


class SpecimenViewSet(LaboratoryModelViewSet):
    queryset = Specimen.objects.all()
    serializer_class = SpecimenSerializer
    required_feature = "lab.specimens"
    filterset_fields = ["specimen_type", "status", "patient_id"]
    search_fields = ["specimen_number", "barcode"]

    def perform_create(self, serializer):
        import uuid

        tenant_id = getattr(self.request, "tenant_id", None)
        obj = serializer.save(
            tenant_id=tenant_id, specimen_number=f"SP-{str(uuid.uuid4()).upper()[:10]}"
        )
        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        canonical_events.emit(
            event_type="cymed.lab.specimen.collected",
            aggregate_type="Specimen",
            aggregate_id=obj.id,
            tenant_id=tenant_id,
            payload={
                "specimen_id": str(obj.id),
                "specimen_number": obj.specimen_number,
                "type": obj.specimen_type,
            },
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
        tenant_id = getattr(self.request, "tenant_id", None)
        obj = serializer.save(tenant_id=tenant_id)
        specimen = obj.specimen
        specimen.status = "rejected"
        specimen.save(update_fields=["status", "updated_at"])
        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        canonical_events.emit(
            event_type="cymed.lab.specimen.rejected",
            aggregate_type="Specimen",
            aggregate_id=specimen.id,
            tenant_id=tenant_id,
            payload={"specimen_id": str(specimen.id), "reason": obj.rejection_reason},
        )


class SpecimenChainOfCustodyViewSet(LaboratoryModelViewSet):
    queryset = SpecimenChainOfCustody.objects.all()
    serializer_class = SpecimenChainOfCustodySerializer
    required_feature = "lab.specimens"
