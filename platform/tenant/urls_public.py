"""
Public, unauthenticated tenant endpoints. Base: /api/v1/public/
Kept separate from urls.py (which is entirely IsPlatformAdmin/auth-gated)
so the auth/tenant-isolation middleware's /api/v1/public/ exemption applies
cleanly to this module only.
"""

from django.urls import path

from platform.tenant import views

urlpatterns = [
    path("demo/provision/", views.demo_provision, name="demo-provision"),
    path("subscriptions/register/", views.subscription_register, name="subscription-register"),
]
