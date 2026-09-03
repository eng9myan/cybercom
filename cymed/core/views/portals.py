from django.shortcuts import render
from django.views.generic import TemplateView


class PatientPortalView(TemplateView):
    template_name = "patient_portal/index.html"


class ProviderPortalView(TemplateView):
    template_name = "provider_portal/index.html"


class MainDashboardView(TemplateView):
    template_name = "dashboard/index.html"
