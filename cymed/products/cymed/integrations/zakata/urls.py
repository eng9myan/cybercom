from django.urls import path

from .views import ZATCAInvoiceViewSet

urlpatterns = [
    path("invoices/", ZATCAInvoiceViewSet.as_view({"get": "list", "post": "create"}), name="zakata-invoice-list"),
    path("invoices/<str:pk>/", ZATCAInvoiceViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="zakata-invoice-detail"),
    path("invoices/<str:pk>/report/", ZATCAInvoiceViewSet.as_view({"post": "report"}), name="zakata-invoice-report"),
    path("invoices/<str:pk>/clear/", ZATCAInvoiceViewSet.as_view({"post": "clear"}), name="zakata-invoice-clear"),
    path("invoices/<str:pk>/generate-qr/", ZATCAInvoiceViewSet.as_view({"post": "generate_qr"}), name="zakata-invoice-qr"),
]
