from django.urls import include, path

urlpatterns = [
    # CRM
    path("crm/accounts/", include("products.cycom.crm.accounts.urls")),
    # Finance
    path("finance/gl/", include("products.cycom.finance.gl.urls")),
    path("finance/ap/", include("products.cycom.finance.ap.urls")),
    path("finance/ar/", include("products.cycom.finance.ar.urls")),
    # Procurement
    path(
        "procurement/purchase-orders/", include("products.cycom.procurement.purchase_orders.urls")
    ),
    path("procurement/vendors/", include("products.cycom.procurement.vendors.urls")),
    # HR
    path("hr/", include("products.cycom.hr.urls")),
    # Payroll
    path("payroll/", include("products.cycom.payroll.urls")),
    # Inventory
    path("inventory/", include("products.cycom.inventory.urls")),
    # Assets
    path("assets/", include("products.cycom.assets.urls")),
    # BI
    path("bi/", include("products.cycom.bi.urls")),
]
