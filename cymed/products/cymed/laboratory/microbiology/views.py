import uuid

from ..views import LaboratoryModelViewSet
from .models import Culture, MicrobiologyResult, Organism, ResistanceProfile, Sensitivity
from .serializers import (
    CultureSerializer,
    MicrobiologyResultSerializer,
    OrganismSerializer,
    ResistanceProfileSerializer,
    SensitivitySerializer,
)


class CultureViewSet(LaboratoryModelViewSet):
    queryset = Culture.objects.prefetch_related("organisms")
    serializer_class = CultureSerializer
    required_feature = "lab.microbiology"
    filterset_fields = ["culture_type", "status"]
    search_fields = ["culture_number"]

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        serializer.save(tenant_id=tenant_id, culture_number=f"CUL-{str(uuid.uuid4()).upper()[:10]}")


class OrganismViewSet(LaboratoryModelViewSet):
    queryset = Organism.objects.prefetch_related("sensitivities", "resistance_profiles")
    serializer_class = OrganismSerializer
    required_feature = "lab.microbiology"
    filterset_fields = ["culture", "gram_stain", "is_contaminant"]


class SensitivityViewSet(LaboratoryModelViewSet):
    queryset = Sensitivity.objects.all()
    serializer_class = SensitivitySerializer
    required_feature = "lab.microbiology"
    filterset_fields = ["organism", "result"]


class ResistanceProfileViewSet(LaboratoryModelViewSet):
    queryset = ResistanceProfile.objects.all()
    serializer_class = ResistanceProfileSerializer
    required_feature = "lab.microbiology"
    filterset_fields = ["organism", "resistance_mechanism", "confirmed"]


class MicrobiologyResultViewSet(LaboratoryModelViewSet):
    queryset = MicrobiologyResult.objects.all()
    serializer_class = MicrobiologyResultSerializer
    required_feature = "lab.microbiology"
