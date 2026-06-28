from django.urls import path
from . import views

urlpatterns = [
    path("customers/", views.CustomerListView.as_view()),
    path("customers/<uuid:pk>/", views.CustomerDetailView.as_view()),
    path("invoices/", views.InvoiceListView.as_view()),
    path("invoices/<uuid:pk>/", views.InvoiceDetailView.as_view()),
    path("invoice-lines/", views.InvoiceLineListView.as_view()),
    path("invoice-lines/<uuid:pk>/", views.InvoiceLineDetailView.as_view()),
    path("payments/", views.PaymentListView.as_view()),
    path("payments/<uuid:pk>/", views.PaymentDetailView.as_view()),
    path("aging-buckets/", views.ARAgingBucketListView.as_view()),
    path("aging-buckets/<uuid:pk>/", views.ARAgingBucketDetailView.as_view()),
]
