from django.urls import path

from .views import AgentMessageView

urlpatterns = [
    path("message/", AgentMessageView.as_view(), name="agent-message"),
]
