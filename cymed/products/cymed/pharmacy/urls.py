"""
CyMed Pharmacy Edition — API URL Configuration
Mounted at: /api/v1/pharmacy/
"""

from django.urls import include, path

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
    # ── Gap-fill (P0-9) ────────────────────────────────────────────
    path("shop/",         include("products.cymed.pharmacy.ecommerce.urls")),
    path("delivery/",     include("products.cymed.pharmacy.delivery.urls")),
    path("pos/",          include("products.cymed.pharmacy.pos_insurance.urls")),
    path("loyalty/",      include("products.cymed.pharmacy.loyalty.urls")),
    path("compounding/",  include("products.cymed.pharmacy.compounding.urls")),
    path("robotics/",     include("products.cymed.pharmacy.robotics.urls")),
]
