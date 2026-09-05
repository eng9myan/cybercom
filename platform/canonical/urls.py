"""
Flavor engine — URL router.
Base: /api/v1/canonical/
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from platform.canonical import views

router = DefaultRouter()
router.register(r"flavors", views.VerticalFlavorViewSet, basename="vertical-flavor")

urlpatterns = [
    path("", include(router.urls)),
]
