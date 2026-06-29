from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.provider_portal.clinical_tasks.views import (
    ClinicalTaskViewSet,
    TaskAssignmentViewSet,
    TaskCommentViewSet,
    TaskEscalationViewSet,
)

router = DefaultRouter()
router.register(r"tasks", ClinicalTaskViewSet, basename="clinical-task")
router.register(r"task-assignments", TaskAssignmentViewSet, basename="task-assignment")
router.register(r"task-comments", TaskCommentViewSet, basename="task-comment")
router.register(r"task-escalations", TaskEscalationViewSet, basename="task-escalation")

urlpatterns = [
    path("", include(router.urls)),
]
