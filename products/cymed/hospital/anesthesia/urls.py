from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.hospital.anesthesia.views import (
    AnesthesiaAssessmentViewSet,
    AnesthesiaPlanViewSet,
    AnesthesiaRecordViewSet,
    RecoveryAssessmentViewSet,
)

router = DefaultRouter()
router.register("assessments", AnesthesiaAssessmentViewSet)
router.register("plans", AnesthesiaPlanViewSet)
router.register("records", AnesthesiaRecordViewSet)
router.register("recovery-assessments", RecoveryAssessmentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
