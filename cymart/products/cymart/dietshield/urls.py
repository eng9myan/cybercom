from django.urls import path

from .views import (
    EvaluateView,
    PlanView,
    ProfileView,
    RegimeListView,
    TodayView,
)

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="dietshield-profile"),
    path("plan/", PlanView.as_view(), name="dietshield-plan"),
    path("regimes/", RegimeListView.as_view(), name="dietshield-regimes"),
    path("today/", TodayView.as_view(), name="dietshield-today"),
    path("evaluate/", EvaluateView.as_view(), name="dietshield-evaluate"),
]
