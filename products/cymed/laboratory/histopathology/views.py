import uuid

from ..views import LaboratoryModelViewSet
from .models import HistologyCase, HistologyDiagnosis, Slide, SlideReview, TissueBlock
from .serializers import (
    HistologyCaseSerializer,
    HistologyDiagnosisSerializer,
    SlideReviewSerializer,
    SlideSerializer,
    TissueBlockSerializer,
)


class HistologyCaseViewSet(LaboratoryModelViewSet):
    queryset = HistologyCase.objects.prefetch_related("blocks")
    serializer_class = HistologyCaseSerializer
    required_feature = "lab.histopathology"
    filterset_fields = ["status"]
    search_fields = ["case_number"]

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        serializer.save(tenant_id=tenant_id, case_number=f"HISTO-{str(uuid.uuid4()).upper()[:8]}")


class TissueBlockViewSet(LaboratoryModelViewSet):
    queryset = TissueBlock.objects.prefetch_related("slides")
    serializer_class = TissueBlockSerializer
    required_feature = "lab.histopathology"


class SlideViewSet(LaboratoryModelViewSet):
    queryset = Slide.objects.prefetch_related("reviews")
    serializer_class = SlideSerializer
    required_feature = "lab.histopathology"
    filterset_fields = ["block", "stain_type", "stain_status"]


class SlideReviewViewSet(LaboratoryModelViewSet):
    queryset = SlideReview.objects.all()
    serializer_class = SlideReviewSerializer
    required_feature = "lab.histopathology"


class HistologyDiagnosisViewSet(LaboratoryModelViewSet):
    queryset = HistologyDiagnosis.objects.all()
    serializer_class = HistologyDiagnosisSerializer
    required_feature = "lab.histopathology"
