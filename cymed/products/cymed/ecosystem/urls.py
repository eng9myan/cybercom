"""CyMed Ecosystem Glue — API URL configuration. Mounted at: /api/v1/ecosystem/"""
from django.urls import include, path

urlpatterns = [
    path("referrals/",       include("products.cymed.ecosystem.referral_routing.urls")),
    path("directory/",       include("products.cymed.ecosystem.provider_directory.urls")),
    path("rewards/",         include("products.cymed.ecosystem.rewards.urls")),
    path("analytics/",       include("products.cymed.ecosystem.analytics.urls")),
    path("capacity/",        include("products.cymed.ecosystem.shared_capacity.urls")),
    path("credentialing/",   include("products.cymed.ecosystem.credentialing.urls")),
]
