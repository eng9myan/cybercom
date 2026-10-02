from django.urls import path

from .agent.views import PartnerAgentTurnView
from .views import PartnerEvaluateView, PartnerPrepareView, PartnerRankView

urlpatterns = [
    path("evaluate/", PartnerEvaluateView.as_view(), name="evaluate"),
    path("rank/", PartnerRankView.as_view(), name="rank"),
    path("prepare/", PartnerPrepareView.as_view(), name="prepare"),
    path("agent/turn/", PartnerAgentTurnView.as_view(), name="agent-turn"),
]
