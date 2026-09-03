from django.urls import path

from .views import ClinicOrderViewSet, ClinicProductViewSet


urlpatterns = [
    path("products/", ClinicProductViewSet.as_view({"get": "list", "post": "create"}),
         name="clinic-prod-list"),
    path("products/<uuid:pk>/", ClinicProductViewSet.as_view(
        {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
         name="clinic-prod-detail"),
    path("orders/", ClinicOrderViewSet.as_view({"get": "list"}), name="clinic-order-list"),
    path("orders/add-to-cart/",
         ClinicOrderViewSet.as_view({"post": "add_to_cart"}), name="clinic-order-add"),
    path("orders/<uuid:pk>/", ClinicOrderViewSet.as_view({"get": "retrieve"}),
         name="clinic-order-detail"),
    path("orders/<uuid:pk>/place/",
         ClinicOrderViewSet.as_view({"post": "place"}), name="clinic-order-place"),
    path("orders/<uuid:pk>/cancel/",
         ClinicOrderViewSet.as_view({"post": "cancel"}), name="clinic-order-cancel"),
    path("orders/<uuid:pk>/ship/",
         ClinicOrderViewSet.as_view({"post": "ship"}), name="clinic-order-ship"),
    path("orders/<uuid:pk>/deliver/",
         ClinicOrderViewSet.as_view({"post": "deliver"}), name="clinic-order-deliver"),
]
