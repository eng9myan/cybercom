from django.urls import path

from .views import CampaignSendViewSet, CampaignViewSet


urlpatterns = [
    path("campaigns/", CampaignViewSet.as_view({"get": "list", "post": "create"}),
         name="mkt-camp-list"),
    path("campaigns/<uuid:pk>/", CampaignViewSet.as_view(
        {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
         name="mkt-camp-detail"),
    path("campaigns/<uuid:pk>/queue-send/",
         CampaignViewSet.as_view({"post": "queue_send"}), name="mkt-camp-queue"),
    path("sends/",       CampaignSendViewSet.as_view({"get": "list"}),  name="mkt-send-list"),
    path("sends/<uuid:pk>/",
         CampaignSendViewSet.as_view({"get": "retrieve"}), name="mkt-send-detail"),
    path("sends/<uuid:pk>/dispatch/",
         CampaignSendViewSet.as_view({"post": "dispatch_"}), name="mkt-send-dispatch"),
]
