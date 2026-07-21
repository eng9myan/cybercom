from django.urls import path

from platform.wallet import views

urlpatterns = [
    path("topup/", views.wallet_topup, name="wallet-topup"),
    path("debit/", views.wallet_debit, name="wallet-debit"),
    path("balance/", views.wallet_balance, name="wallet-balance"),
]
