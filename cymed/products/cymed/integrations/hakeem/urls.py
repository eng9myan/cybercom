from django.urls import path

from .views import HakeemLookupView, HakeemMessageViewSet


urlpatterns = [
    path("lookup/", HakeemLookupView.as_view(), name="hakeem-lookup"),
    path("messages/",
         HakeemMessageViewSet.as_view({"get": "list"}), name="hakeem-msg-list"),
    path("messages/<uuid:pk>/",
         HakeemMessageViewSet.as_view({"get": "retrieve"}), name="hakeem-msg-detail"),
]
