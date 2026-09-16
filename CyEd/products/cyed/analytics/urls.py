from django.urls import path

from products.cyed.analytics.views import (
    AtRiskView,
    CampusComparisonView,
    DashboardView,
    FeeRiskView,
)

urlpatterns = [
    path("at-risk/", AtRiskView.as_view(), name="analytics-at-risk"),
    path("fee-risk/", FeeRiskView.as_view(), name="analytics-fee-risk"),
    path("dashboard/", DashboardView.as_view(), name="analytics-dashboard"),
    path(
        "campus-comparison/",
        CampusComparisonView.as_view(),
        name="analytics-campus-comparison",
    ),
]
