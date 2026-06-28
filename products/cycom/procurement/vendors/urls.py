from django.urls import path
from . import views

urlpatterns = [
    path("qualifications/", views.VendorQualificationListView.as_view(), name="vendor-qualification-list"),
    path("qualifications/<uuid:pk>/", views.VendorQualificationDetailView.as_view(), name="vendor-qualification-detail"),
    path("performances/", views.VendorPerformanceListView.as_view(), name="vendor-performance-list"),
    path("performances/<uuid:pk>/", views.VendorPerformanceDetailView.as_view(), name="vendor-performance-detail"),
]
