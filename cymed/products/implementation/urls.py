from rest_framework.routers import DefaultRouter

from .views import (
    CutoverChecklistViewSet,
    HypercareLogViewSet,
    ImplementationProjectViewSet,
    MethodologyTemplateViewSet,
    ProjectMilestoneViewSet,
    ProjectTaskViewSet,
)

router = DefaultRouter()
router.register("projects", ImplementationProjectViewSet, basename="implementation-project")
router.register("milestones", ProjectMilestoneViewSet, basename="project-milestone")
router.register("tasks", ProjectTaskViewSet, basename="project-task")
router.register("cutover-checklists", CutoverChecklistViewSet, basename="cutover-checklist")
router.register("hypercare-logs", HypercareLogViewSet, basename="hypercare-log")
router.register("templates", MethodologyTemplateViewSet, basename="methodology-template")

urlpatterns = router.urls
