from django.urls import path

from .views import (
    InsurancePolicyViewSet,
    PatientWalletView,
    PaymentMethodViewSet,
    PaymentRequestPublicView,
    PreAuthorizationViewSet,
    UnifiedBillViewSet,
)


def _vs(vs, actions):
    return vs.as_view(actions)


urlpatterns = [
    # Bills
    path("bills/", _vs(UnifiedBillViewSet, {"get": "list"}), name="bill-list"),
    path("bills/<uuid:pk>/", _vs(UnifiedBillViewSet, {"get": "retrieve"}), name="bill-detail"),
    path("bills/<uuid:pk>/pay/",
         _vs(UnifiedBillViewSet, {"post": "pay"}), name="bill-pay"),
    path("bills/<uuid:pk>/payment-request/",
         _vs(UnifiedBillViewSet, {"post": "request_payment"}), name="bill-payment-request"),

    # Payment request (public — no auth)
    path("payment-requests/<str:token>/",
         PaymentRequestPublicView.as_view(), name="payment-request-public"),

    # Payment methods
    path("payment-methods/",
         _vs(PaymentMethodViewSet, {"get": "list", "post": "create"}),
         name="payment-method-list"),
    path("payment-methods/<uuid:pk>/",
         _vs(PaymentMethodViewSet, {"get": "retrieve", "delete": "destroy"}),
         name="payment-method-detail"),
    path("payment-methods/<uuid:pk>/default/",
         _vs(PaymentMethodViewSet, {"post": "set_default"}),
         name="payment-method-default"),

    # Wallet
    path("wallet/", PatientWalletView.as_view(), name="wallet"),

    # Insurance
    path("insurance/",
         _vs(InsurancePolicyViewSet, {"get": "list", "post": "create"}),
         name="insurance-list"),
    path("insurance/<uuid:pk>/",
         _vs(InsurancePolicyViewSet,
             {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
         name="insurance-detail"),
    path("insurance/<uuid:pk>/verify/",
         _vs(InsurancePolicyViewSet, {"post": "verify"}), name="insurance-verify"),
    path("insurance/<uuid:pk>/eligibility/",
         _vs(InsurancePolicyViewSet, {"post": "eligibility"}), name="insurance-eligibility"),
    path("insurance/<uuid:pk>/preauth/",
         _vs(InsurancePolicyViewSet, {"post": "preauth"}), name="insurance-preauth"),
    path("preauths/",
         _vs(PreAuthorizationViewSet, {"get": "list"}), name="preauth-list"),
    path("preauths/<uuid:pk>/",
         _vs(PreAuthorizationViewSet, {"get": "retrieve"}), name="preauth-detail"),
]
