from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"requests", views.ApprovalRequestViewSet, basename="approval-request")
router.register(r"workflows", views.ApprovalWorkflowViewSet, basename="approval-workflow")
router.register(r"decisions", views.ApprovalDecisionViewSet, basename="approval-decision")
router.register(r"audit-log", views.ApprovalAuditLogViewSet, basename="approval-audit-log")

urlpatterns = [path("", include(router.urls))]
