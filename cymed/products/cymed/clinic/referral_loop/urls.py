from django.urls import path

from .views import ReferralViewSet


urlpatterns = [
    path("", ReferralViewSet.as_view({"get": "list"}), name="referral-list"),
    path("send/", ReferralViewSet.as_view({"post": "send"}), name="referral-send"),
    path("<uuid:pk>/", ReferralViewSet.as_view({"get": "retrieve", "put": "update"}),
         name="referral-detail"),
    path("<uuid:pk>/acknowledge/",
         ReferralViewSet.as_view({"post": "acknowledge"}), name="referral-ack"),
    path("<uuid:pk>/schedule/",
         ReferralViewSet.as_view({"post": "schedule"}), name="referral-sched"),
    path("<uuid:pk>/complete/",
         ReferralViewSet.as_view({"post": "complete"}), name="referral-complete"),
    path("<uuid:pk>/share-result/",
         ReferralViewSet.as_view({"post": "share_result"}), name="referral-share"),
]
