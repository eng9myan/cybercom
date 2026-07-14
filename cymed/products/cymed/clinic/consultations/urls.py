from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.clinic.consultations.views import (
    ConsultationAttachmentViewSet,
    ConsultationDiagnosisViewSet,
    ConsultationFollowUpViewSet,
    ConsultationPlanViewSet,
    ConsultationProcedureViewSet,
    ConsultationViewSet,
)

router = DefaultRouter()
router.register("notes", ConsultationViewSet)
router.register("diagnoses", ConsultationDiagnosisViewSet)
router.register("procedures", ConsultationProcedureViewSet)
router.register("plans", ConsultationPlanViewSet)
router.register("follow-ups", ConsultationFollowUpViewSet)
router.register("attachments", ConsultationAttachmentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
