from django.urls import path

from . import views

urlpatterns = [
    path("categories/", views.AssetCategoryListView.as_view(), name="asset-category-list"),
    path(
        "categories/<uuid:pk>/",
        views.AssetCategoryDetailView.as_view(),
        name="asset-category-detail",
    ),
    path("", views.FixedAssetListView.as_view(), name="fixed-asset-list"),
    path("<uuid:pk>/", views.FixedAssetDetailView.as_view(), name="fixed-asset-detail"),
    path("depreciations/", views.DepreciationListView.as_view(), name="depreciation-list"),
    path(
        "depreciations/<uuid:pk>/",
        views.DepreciationDetailView.as_view(),
        name="depreciation-detail",
    ),
]
