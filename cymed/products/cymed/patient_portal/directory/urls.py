from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"hospitals", views.HospitalListingViewSet, basename="dir-hospital")
router.register(r"clinics", views.ClinicListingViewSet, basename="dir-clinic")
router.register(r"specialties", views.ClinicSpecialtyViewSet, basename="dir-specialty")
router.register(r"laboratories", views.LaboratoryListingViewSet, basename="dir-laboratory")
router.register(
    r"imaging-centers", views.ImagingCenterListingViewSet, basename="dir-imaging-center"
)
router.register(r"pharmacies", views.PharmacyListingViewSet, basename="dir-pharmacy")
router.register(r"reviews", views.ProviderReviewViewSet, basename="dir-review")

urlpatterns = [path("", include(router.urls))]
