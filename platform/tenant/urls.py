from django.urls import path
from . import views

urlpatterns = [
    path("", views.TenantListView.as_view(), name="tenant-list"),
    path("<uuid:pk>/", views.TenantDetailView.as_view(), name="tenant-detail"),
]
