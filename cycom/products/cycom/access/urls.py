from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.access.views import AccessGrantViewSet, RoleAssignmentViewSet, RoleViewSet

router = DefaultRouter()
router.register("roles", RoleViewSet)
router.register("role-assignments", RoleAssignmentViewSet)
router.register("grants", AccessGrantViewSet)

urlpatterns = [path("", include(router.urls))]
