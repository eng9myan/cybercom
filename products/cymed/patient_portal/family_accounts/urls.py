from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'groups', views.FamilyGroupViewSet, basename='family-group')
router.register(r'members', views.FamilyMemberViewSet, basename='family-member')
router.register(r'access-permissions', views.FamilyAccessPermissionViewSet, basename='family-access-permission')
router.register(r'dependent-profiles', views.DependentProfileViewSet, basename='family-dependent-profile')

urlpatterns = [path('', include(router.urls))]
