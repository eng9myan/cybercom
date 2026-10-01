from django.urls import path

from .views import CatalogSearchView, MerchantDetailView, MerchantListView

urlpatterns = [
    path("", MerchantListView.as_view(), name="merchants-list"),
    path("search/", CatalogSearchView.as_view(), name="merchants-search"),
    path("<uuid:merchant_id>/", MerchantDetailView.as_view(), name="merchants-detail"),
]
