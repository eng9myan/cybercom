from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.health.views import (
    ActionPlanViewSet,
    HealthRecordViewSet,
    ImmunisationDoseViewSet,
    ImmunisationRecordViewSet,
    MedicalIncidentViewSet,
    MedicationAdministrationViewSet,
    MedicationAuthorityViewSet,
    SickBayVisitViewSet,
)

router = DefaultRouter()
router.register("records", HealthRecordViewSet)
router.register("incidents", MedicalIncidentViewSet)
router.register("action-plans", ActionPlanViewSet)
router.register("sick-bay", SickBayVisitViewSet)
router.register("immunisations", ImmunisationRecordViewSet)
router.register("immunisation-doses", ImmunisationDoseViewSet)
router.register("medication-authorities", MedicationAuthorityViewSet)
router.register("medication-log", MedicationAdministrationViewSet)

urlpatterns = [path("", include(router.urls))]
