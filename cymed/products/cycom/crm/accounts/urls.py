from django.urls import path

from . import views

urlpatterns = [
    path("", views.CRMAccountListView.as_view()),
    path("<uuid:pk>/", views.CRMAccountDetailView.as_view()),
    path("contacts/", views.AccountContactListView.as_view()),
    path("contacts/<uuid:pk>/", views.AccountContactDetailView.as_view()),
]
