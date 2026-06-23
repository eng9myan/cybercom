"""
CyMed Pharmacy Edition — API URL Configuration
Mounted at: /api/v1/pharmacy/
"""
from django.urls import path, include

urlpatterns = [
    # Prescription Management
    path("prescriptions/", include("products.cymed.pharmacy.prescriptions.urls")),

    # Dispensing
    path("dispensing/", include("products.cymed.pharmacy.dispensing.urls")),

    # Clinical Pharmacy
    path("clinical/", include("products.cymed.pharmacy.clinical_pharmacy.urls")),

    # Medication Reconciliation
    path("reconciliation/", include("products.cymed.pharmacy.medication_reconciliation.urls")),

    # Drug Interactions
    path("interactions/", include("products.cymed.pharmacy.drug_interactions.urls")),

    # Formulary Management
    path("formulary/", include("products.cymed.pharmacy.formulary.urls")),

    # Pharmacy Automation (ADC, Robots)
    path("automation/", include("products.cymed.pharmacy.automation.urls")),

    # Analytics & Dashboards
    path("analytics/", include("products.cymed.pharmacy.analytics.urls")),

    # Inventory Bridge (CyCom ERP)
    path("inventory/", include("products.cymed.pharmacy.inventory_bridge.urls")),

    # Procurement Bridge (CyCom ERP)
    path("procurement/", include("products.cymed.pharmacy.procurement_bridge.urls")),
]
