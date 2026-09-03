from django.urls import path

from .views import JoFawTraInvoiceViewSet

urlpatterns = [
    path("invoices/", JoFawTraInvoiceViewSet.as_view({"get": "list", "post": "create"}), name="jofawtra-invoice-list"),
    path("invoices/<str:pk>/", JoFawTraInvoiceViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="jofawtra-invoice-detail"),
    path("invoices/<str:pk>/submit/", JoFawTraInvoiceViewSet.as_view({"post": "submit"}), name="jofawtra-invoice-submit"),
    path("invoices/<str:pk>/status/", JoFawTraInvoiceViewSet.as_view({"get": "check_status"}), name="jofawtra-invoice-status"),
]
