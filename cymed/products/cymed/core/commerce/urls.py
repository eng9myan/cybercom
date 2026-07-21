from django.urls import path

from products.cymed.core.commerce.views import cross_network_checkout

urlpatterns = [
    path("checkout/", cross_network_checkout, name="cross-network-checkout"),
]
