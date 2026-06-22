from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.clinic.consultations.views import (
    ConsultationViewSet, ConsultationDiagnosisViewSet, ConsultationProcedureViewSet,
    ConsultationPlanViewSet, ConsultationFollowUpViewSet, ConsultationAttachmentViewSet
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
