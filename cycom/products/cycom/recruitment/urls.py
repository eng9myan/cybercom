from rest_framework.routers import DefaultRouter

from products.cycom.recruitment.views import ApplicantViewSet

router = DefaultRouter()
router.register("applicants", ApplicantViewSet, basename="recruitment-applicant")

urlpatterns = router.urls
