import uuid

from ..views import LaboratoryModelViewSet
from .models import (
    GrossExamination,
    MicroscopicExamination,
    PathologyCase,
    PathologyDiagnosis,
    PathologySpecimen,
)
from .serializers import (
    GrossExaminationSerializer,
    MicroscopicExaminationSerializer,
    PathologyCaseSerializer,
    PathologyDiagnosisSerializer,
    PathologySpecimenSerializer,
)


class PathologyCaseViewSet(LaboratoryModelViewSet):
    queryset = PathologyCase.objects.prefetch_related("specimens")
    serializer_class = PathologyCaseSerializer
    required_feature = "lab.pathology"
    filterset_fields = ["status", "assigned_pathologist", "priority", "is_intraoperative"]
    search_fields = ["case_number"]

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        serializer.save(
            tenant_id=tenant_id,
            case_number=f"PATH-{str(uuid.uuid4()).upper()[:10]}",
            patient_id=self.request.data.get("patient_id"),
        )


class PathologySpecimenViewSet(LaboratoryModelViewSet):
    queryset = PathologySpecimen.objects.all()
    serializer_class = PathologySpecimenSerializer
    required_feature = "lab.pathology"


class GrossExaminationViewSet(LaboratoryModelViewSet):
    queryset = GrossExamination.objects.all()
    serializer_class = GrossExaminationSerializer
    required_feature = "lab.pathology"


class MicroscopicExaminationViewSet(LaboratoryModelViewSet):
    queryset = MicroscopicExamination.objects.all()
    serializer_class = MicroscopicExaminationSerializer
    required_feature = "lab.pathology"


class PathologyDiagnosisViewSet(LaboratoryModelViewSet):
    queryset = PathologyDiagnosis.objects.all()
    serializer_class = PathologyDiagnosisSerializer
    required_feature = "lab.pathology"
