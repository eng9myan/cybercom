from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.customfields.views import (
    CustomFieldDefinitionViewSet,
    CustomFieldRegistryView,
    CustomFieldValuesView,
)

router = DefaultRouter()
router.register("definitions", CustomFieldDefinitionViewSet, basename="customfield-definition")

urlpatterns = [
    path("registry/", CustomFieldRegistryView.as_view(), name="customfield-registry"),
    path("values/", CustomFieldValuesView.as_view(), name="customfield-values"),
    path("", include(router.urls)),
]
