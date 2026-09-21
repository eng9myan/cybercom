from django.urls import path

from products.cycom.storefront import views

urlpatterns = [
    path("<slug:slug>/products/", views.product_list, name="storefront-products"),
    path("<slug:slug>/carts/", views.create_cart, name="storefront-cart-create"),
    path("<slug:slug>/carts/<str:token>/", views.cart_detail, name="storefront-cart-detail"),
    path("<slug:slug>/carts/<str:token>/items/", views.cart_add_item, name="storefront-cart-add-item"),
    path(
        "<slug:slug>/carts/<str:token>/items/<uuid:product_id>/",
        views.cart_remove_item,
        name="storefront-cart-remove-item",
    ),
    path("<slug:slug>/carts/<str:token>/checkout/", views.cart_checkout, name="storefront-cart-checkout"),
]
