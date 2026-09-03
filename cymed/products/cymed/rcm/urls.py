from django.urls import path

from .views import (
    AppealCaseViewSet,
    Claim837ViewSet,
    ClaimResponseViewSet,
    DenialCodeViewSet,
    DenialsListView,
    KPIView,
)


urlpatterns = [
    path("claims/",             Claim837ViewSet.as_view({"get": "list"}),
         name="rcm-claim-list"),
    path("claims/build/",       Claim837ViewSet.as_view({"post": "build"}),
         name="rcm-claim-build"),
    path("claims/<uuid:pk>/",   Claim837ViewSet.as_view({"get": "retrieve",
                                                          "put": "update",
                                                          "patch": "partial_update"}),
         name="rcm-claim-detail"),
    path("claims/<uuid:pk>/scrub/",
         Claim837ViewSet.as_view({"post": "scrub"}), name="rcm-claim-scrub"),
    path("claims/<uuid:pk>/predict-denial/",
         Claim837ViewSet.as_view({"post": "predict_denial"}), name="rcm-claim-predict"),
    path("claims/<uuid:pk>/submit/",
         Claim837ViewSet.as_view({"post": "submit"}), name="rcm-claim-submit"),
    path("claims/<uuid:pk>/appeal/",
         Claim837ViewSet.as_view({"post": "appeal"}), name="rcm-claim-appeal"),

    path("responses/",
         ClaimResponseViewSet.as_view({"get": "list"}), name="rcm-response-list"),
    path("responses/<uuid:pk>/",
         ClaimResponseViewSet.as_view({"get": "retrieve"}), name="rcm-response-detail"),

    path("appeals/", AppealCaseViewSet.as_view({"get": "list"}), name="rcm-appeal-list"),
    path("appeals/<uuid:pk>/",
         AppealCaseViewSet.as_view({"get": "retrieve"}), name="rcm-appeal-detail"),

    path("denials/",       DenialsListView.as_view(), name="rcm-denials"),
    path("denial-codes/",  DenialCodeViewSet.as_view({"get": "list"}), name="rcm-denial-code-list"),
    path("kpis/",           KPIView.as_view(),          name="rcm-kpis"),
]
