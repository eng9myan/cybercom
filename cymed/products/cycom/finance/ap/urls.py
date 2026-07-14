from django.urls import path

from . import views

urlpatterns = [
    path("vendors/", views.VendorListView.as_view()),
    path("vendors/<uuid:pk>/", views.VendorDetailView.as_view()),
    path("bills/", views.BillListView.as_view()),
    path("bills/<uuid:pk>/", views.BillDetailView.as_view()),
    path("bill-lines/", views.BillLineListView.as_view()),
    path("bill-lines/<uuid:pk>/", views.BillLineDetailView.as_view()),
    path("vendor-payments/", views.VendorPaymentListView.as_view()),
    path("vendor-payments/<uuid:pk>/", views.VendorPaymentDetailView.as_view()),
]
