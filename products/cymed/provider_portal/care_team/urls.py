from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'teams', views.CareTeamViewSet, basename='care-team')
router.register(r'members', views.CareTeamMemberViewSet, basename='care-team-member')
router.register(r'assignments', views.CareTeamAssignmentViewSet, basename='care-team-assignment')
router.register(r'roles', views.CareTeamRoleViewSet, basename='care-team-role')
router.register(r'coverage-schedules', views.CoverageScheduleViewSet, basename='coverage-schedule')

urlpatterns = [path('', include(router.urls))]
