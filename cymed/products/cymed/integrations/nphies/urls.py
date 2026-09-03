from django.urls import path

from .views import NphiesInteractionViewSet


urlpatterns = [
    path("interactions/",
         NphiesInteractionViewSet.as_view({"get": "list"}),
         name="nphies-interaction-list"),
    path("interactions/<uuid:pk>/",
         NphiesInteractionViewSet.as_view({"get": "retrieve"}),
         name="nphies-interaction-detail"),
]
