from django.urls import path

from .views import SuggestCodesView


urlpatterns = [
    path("suggest/", SuggestCodesView.as_view(), name="clinic-auto-coding-suggest"),
]
