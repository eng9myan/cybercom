from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.ai_agents.views import (
    AgentDefinitionViewSet,
    AgentInteractionLogViewSet,
    DifferentiatorGenerateView,
    GeneratedArtifactViewSet,
    IntegrityReviewViewSet,
    LessonPlannerGenerateView,
    RubricGenerateView,
    SocraticAskView,
    TutorAskView,
)

router = DefaultRouter()
router.register("agents", AgentDefinitionViewSet)
router.register("interactions", AgentInteractionLogViewSet)
router.register("artifacts", GeneratedArtifactViewSet)
router.register("integrity/reviews", IntegrityReviewViewSet)

urlpatterns = [
    path("tutor/ask/", TutorAskView.as_view(), name="tutor-ask"),
    path("tutor/socratic/", SocraticAskView.as_view(), name="tutor-socratic"),
    path("lesson-planner/generate/", LessonPlannerGenerateView.as_view(), name="lesson-planner-generate"),
    path("rubric/generate/", RubricGenerateView.as_view(), name="rubric-generate"),
    path("differentiator/generate/", DifferentiatorGenerateView.as_view(), name="differentiator-generate"),
    path("", include(router.urls)),
]
