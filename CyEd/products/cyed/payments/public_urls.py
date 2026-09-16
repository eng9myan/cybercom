"""
Unauthenticated payment routes.

Kept in their own module so that mounting them is an explicit, greppable act.
Anything added here is reachable without a bearer token and without a tenant
header — it must carry its own proof of origin (the webhook uses HMAC-SHA256
over the raw request body) and must resolve its own tenant.
"""

from django.urls import path

from products.cyed.payments.views import payment_webhook

urlpatterns = [
    path("webhook/<str:provider>/", payment_webhook, name="payment-webhook"),
]
