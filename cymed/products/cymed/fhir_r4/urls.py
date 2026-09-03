from django.urls import path

from .views import BundleView, CapabilityView, ResourceView


urlpatterns = [
    path("metadata",              CapabilityView.as_view(),   name="fhir-metadata"),
    path("",                       BundleView.as_view(),        name="fhir-bundle"),
    path("<str:resource_type>",   ResourceView.as_view(),      name="fhir-search"),
    path("<str:resource_type>/<uuid:id>", ResourceView.as_view(), name="fhir-instance"),
]
