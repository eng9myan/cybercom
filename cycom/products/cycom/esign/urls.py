"""
CyCom E-Signature — URL Router.
Mounted at /api/sign/ (not /api/v1/) to match the existing frontend
rewrite in cycom-erp/next.config.ts, which was already scaffolded against
that exact path before the backend existed.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.esign import views

router = DefaultRouter()
router.register(r"templates", views.SignTemplateViewSet, basename="sign-template")
router.register(r"requests", views.SignRequestViewSet, basename="sign-request")

urlpatterns = [
    # Public token routes must be registered before the router include —
    # DefaultRouter's requests/<pk>/ detail route would otherwise greedily
    # match "public" as a pk and 404 before reaching these views.
    path(
        "requests/public/<str:token>/sign",
        views.public_sign_submit,
        name="sign-request-public-submit",
    ),
    path(
        "requests/public/<str:token>",
        views.public_sign_detail,
        name="sign-request-public-detail",
    ),
    path("", include(router.urls)),
]
