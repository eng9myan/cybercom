from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.sis.views import (
    AcademicYearViewSet,
    ClassSectionViewSet,
    EnrolmentViewSet,
    FamilyViewSet,
    GuardianViewSet,
    StudentViewSet,
)

router = DefaultRouter()
router.register("academic-years", AcademicYearViewSet)
router.register("guardians", GuardianViewSet)
router.register("families", FamilyViewSet)
router.register("students", StudentViewSet)
router.register("class-sections", ClassSectionViewSet)
router.register("enrolments", EnrolmentViewSet)

urlpatterns = [path("", include(router.urls))]
