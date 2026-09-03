from django.urls import path

from .views import (
    CDSAlertViewSet,
    FallRiskView,
    ICDSuggestionViewSet,
    ICDSuggestView,
    InteractionCheckView,
    NEWS2View,
    ReadmissionView,
    RiskScoreViewSet,
    SepsisView,
)


urlpatterns = [
    # Compute endpoints
    path("interactions/check/",  InteractionCheckView.as_view(), name="cds-interactions"),
    path("scores/news2/",         NEWS2View.as_view(),             name="cds-news2"),
    path("scores/sepsis/",        SepsisView.as_view(),            name="cds-sepsis"),
    path("scores/readmission/",   ReadmissionView.as_view(),       name="cds-readmission"),
    path("scores/fall-risk/",     FallRiskView.as_view(),          name="cds-fall-risk"),
    path("icd/suggest/",          ICDSuggestView.as_view(),        name="cds-icd-suggest"),

    # Persistence read-only
    path("alerts/",               CDSAlertViewSet.as_view({"get": "list"}), name="cds-alert-list"),
    path("alerts/<uuid:pk>/",     CDSAlertViewSet.as_view({"get": "retrieve"}), name="cds-alert-detail"),
    path("alerts/<uuid:pk>/acknowledge/",
         CDSAlertViewSet.as_view({"post": "acknowledge"}), name="cds-alert-ack"),
    path("scores/",               RiskScoreViewSet.as_view({"get": "list"}), name="cds-score-list"),
    path("scores/<uuid:pk>/",     RiskScoreViewSet.as_view({"get": "retrieve"}), name="cds-score-detail"),
    path("icd/suggestions/",      ICDSuggestionViewSet.as_view({"get": "list"}), name="cds-icd-list"),
    path("icd/suggestions/<uuid:pk>/",
         ICDSuggestionViewSet.as_view({"get": "retrieve"}), name="cds-icd-detail"),
]
