from django.urls import path
from . import views

urlpatterns = [
    path("accounts/", views.AccountListView.as_view()),
    path("accounts/<uuid:pk>/", views.AccountDetailView.as_view()),
    path("journal-entries/", views.JournalEntryListView.as_view()),
    path("journal-entries/<uuid:pk>/", views.JournalEntryDetailView.as_view()),
    path("journal-lines/", views.JournalLineListView.as_view()),
    path("journal-lines/<uuid:pk>/", views.JournalLineDetailView.as_view()),
]
