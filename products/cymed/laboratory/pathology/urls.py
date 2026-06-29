from rest_framework.routers import DefaultRouter

from .views import (
    GrossExaminationViewSet,
    MicroscopicExaminationViewSet,
    PathologyCaseViewSet,
    PathologyDiagnosisViewSet,
    PathologySpecimenViewSet,
)

router = DefaultRouter()
router.register("cases", PathologyCaseViewSet, basename="lab-path-cases")
router.register("specimens", PathologySpecimenViewSet, basename="lab-path-specimens")
router.register("gross-examinations", GrossExaminationViewSet, basename="lab-gross-exams")
router.register(
    "microscopic-examinations", MicroscopicExaminationViewSet, basename="lab-micro-exams"
)
router.register("diagnoses", PathologyDiagnosisViewSet, basename="lab-path-diagnoses")

urlpatterns = router.urls
