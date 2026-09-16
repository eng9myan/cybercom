from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.gradebook.views import (
    AssessmentViewSet,
    GradeViewSet,
    RubricCriterionViewSet,
    RubricLevelViewSet,
    RubricViewSet,
)

router = DefaultRouter()
router.register("assessments", AssessmentViewSet)
router.register("grades", GradeViewSet)
router.register("rubrics", RubricViewSet)
router.register("rubric-criteria", RubricCriterionViewSet)
router.register("rubric-levels", RubricLevelViewSet)

urlpatterns = [path("", include(router.urls))]
